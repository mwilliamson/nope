The Nope Programming Language
=============================

Nope is a statically-typed subset of Python 3 that can be compiled to multiple targets.
At the moment, Python, node.js and C# are supported with varying degrees of feature-completeness.
Any valid Nope program can be run directly as a Python 3 program.

The static types are expressed using comments, rather than annotations, for
several reasons:

* This means the static typing has no effect at runtime, allowing Nope programs
  to be run directly as Python 3 programs without any extra dependencies or
  performance penalty.

* A separate syntax can be used within the comments to succinctly express types,
  rather than (ab)using existing Python syntax.

* It can be useful to decouple the signature of a function from the implementation.
  For instance, using separate comments makes it easy to type a function such
  that it only accepts arguments by positions rather than keyword.

Here's an example of calculating Fibonacci numbers using Nope:

.. code-block:: python

    #:: int -> int
    def fib(n):
        seq = [0, 1]
        for i in range(2, n + 1):
            seq.append(seq[i - 1] + seq[i - 2])
        
        return seq[n]

    print(fib(10))

TODO
----

* When defining `__add__` and similar methods on classes,
  the type signature should be specific e.g. on int, ``int -> int``.
  However, to maintain compatibility with Python,
  the type checker should assume the argument is the top type when type
  checking the actual method, so isinstance or similar still has to be used.

* Support for the r versions of operators e.g. ``__radd__``.

* Inheritance

* Define builtin types and functions and the standard library in nope where possible,
  define a minimal set of types and functions (such as integers) per-platform.

* A way of specifying dependencies on a per-platform basis to allow shimming
  of existing libraries into a common interface.

* If a class definition body contains a value of type object that could
  be a function (but that is not possible to determine at runtime), how
  should it be treated? In Python, if it's a function, we bind it to the
  instance. Is it possible to sensibly do the same in other languages?
  The result is that any value of type object will need to be checked
  as to whether it is a function or not for consistency.

* Proper tests for builtin functions

* Prevent re-definition of functions and classes

* Ensure that all signatures are used in typing rules

* The type of a variable can change as it is assigned to in a function.
  We need to make sure that the type is consistent if that variable is captured
  in a function definition.

* If a variable is deleted (including the implicit delete at the end of an
  exception handler), we should prevent it from being captured in functions.

* Prevent re-definition of types and functions.

* Check type of loops twice, in case assignments in the body of the loop change the type of variables.
  Or just don't let the type change.
  
* Find a way to speed up the C# tests. Record/replay?

* Explicitly unique ID to each node rather than relying on builtin id.

* Split out stages:

  * Generate module DAG (based on imports)
  
  * Generate type identifiers, as distinct from type info generated later to
    remove circularity

* Change ``collections.namedtuple()` transformer to require a distinct type
  annotation e.g. ``:field str`` so that ``::str`` is unambiguously typing
  the following expression.

Status
------

Syntax
~~~~~~

This section describes support for parsing and type-checking each of
`Python 3.4's syntax nodes <https://docs.python.org/3.4/library/ast.html#abstract-grammar>`_.
Note that not all backends may support all features.

* **Function definitions**: partially supported.

  * **name**: supported.
  
  * **arguments**: partially supported.
    Positional and keyword arguments are supported, but nothing else
    (default values, ``*args``, ``**kwargs``, keyword-only arguments).
    
  * **body**: supported.
  
  * **decorators**: unsupported.
  
  * **annotations**: unsupported (both argument and return annotations).
  
  The signature of a function should be specified by a signature comment immediately before the function definition.
  For instance:
  
  .. code-block:: python

      #:: int -> int
      def increment(x):
          return x + 1
      
      #:: int, str -> none
      def repeated_greeting(repeat, message):
          for i in range(0, repeat):
              print(message)
      
      #:: repeat: int, message: str -> none
      def repeated_greeting(repeat, message):
          for i in range(0, repeat):
              print(message)

* **Class definitions**: partially supported.
  Most notably, inheritance, metaclasses and dynamic gubbins such as ``__getattr__``
  are unsupported.

* **Return statements**: supported.

* **Delete statements**: unsupported.

* **Assignments**: partially supported.
  Assignments to variables (e.g. ``x``), elements of sequences (e.g. ``x[i]``), and attributes (e.g. ``x.y``)
  are supported, but not assignment to slices (e.g. ``x[:]``).

* **Augmented assignments**: unsupported.

* **For loops**: supported.
  
* **While loops**: supported.

* **If statements**: supported.

* **With statements**: supported.

* **Raise statements**: partially supported.
  Only statements in the form ``raise value`` are supported.
  ``raise``, ``raise ExceptionType`` and ``raise value1 from value2`` are unsupported.

* **Try statements**: partially supported.
  Tuples of exceptions are not supported when specifying the type in exception handlers.
  The ``else`` branch is ignored.

* **Assert statements**: supported.

* **Import statements**: partially supported.
  The various forms of import statement are supported.
  However, only local modules and a subset of the standard library are currently supported.
  Modules from dependencies are unsupported.
  
* **global keyword**: unsupported.

* **nonlocal keyword**: unsupported.

* **Expression statements**: supported.

* **pass keyword**: supported.

* **break keyword**: supported.

* **continue keyword**: supported.

With statements
~~~~~~~~~~~~~~~

Consider the following:

.. code-block:: python

    with x:
        y = f()
        
    g(y)

It isn't guaranteed that ``y`` has been assigned a value since ``f()`` could
raise an exception that is then suppressed by the context manager's ``__exit__`` method.
Therefore, ``g(y)`` fails to type-check.
(If the exception isn't suppressed by the ``__exit__`` method, we can safely
assume treat the variable as assigned since we won't be executing any code after the exception).
However, in the common case, we'd like to be able to assume that the variable has been assigned,
and such an assumption is safe in many cases, such as:

.. code-block:: python

    with open(path) as file_:
        contents = file_.read()
    
    print(contents)

We can allow such examples to type-check by inspecting the type of ``__exit__``.
If its return type is ``none``, then it is guaranteed to return a false value,
meaning it will never suppress exceptions.


Python
~~~~~~

Any valid Nope program should be directly executable using Python 3.4.
The best way to support earlier versions of Python is in the same way as you would
on a normal Python 3.4 codebase i.e. avoiding features unsupported in earlier versions.

Node.js backend
~~~~~~~~~~~~~~~

Supported builtin functions:

* ``abs``: supported

* ``bool``: partially supported. The magic method ``__bool__`` is ignored.

* ``iter``: partially supported. The sequence protocol is unsupported.

* ``print``: only a single argument is accepted.

Unimplemented optimisations:

* If the result of boolean operations ('and' or 'or') is only used as a
  condition, such as the condition of an 'if' statement or 'while' loop,
  then the value can simply be true or false rather than the actual value
  of the operation. In other words, ``x and y`` can be optimised to
  ``bool(x) && bool(y)``.

* Unless ``bool()`` has been explicitly invoked, booleans, strings and integers
  can be used directly if only used for their truth value e.g. in if statement
  conditions.

* Avoid re-evaluating bool(value) if boolean operations are used directly in
  conditions. For instance, in ``if x and y``, ``bool(x)`` only needs to be
  evaluated once, even if ``bool(x)`` is ``True``. (A naive implementation
  evalutes ``bool(x)`` once for the ``and`` operation, which would have the
  value of ``x``, causing ``bool(x)`` to be evaluated again as the condition
  of the ``if`` statement.)


Differences from Python 3
-------------------------

Subclassing builtins
~~~~~~~~~~~~~~~~~~~~~

Nope does not allow subclassing of some builtins,
such as ``int`` and ``list``.
This restraint means a value of type ``int`` is guaranteed to have the concrete type ``int`` rather than a subclass of ``int``,
allowing certain optimisations to be used when generating code.

Nested classes
~~~~~~~~~~~~~~

Nope currently only supports classes defined in module scope.
Although definitions within other statements, such as a function,
aren't prohibited, they are likely to exhibit strange behaviour with
respect to the type system.

Tests
-----

Run the tests with the command `make test`.

By default, backends are tested by spawning a new process for each test program.
Set the environment variable `TEST_FAST` to `1` (e.g. `TEST_FAST=1 make test`) to
reuse the same process for multiple programs.
This should make the tests run significantly faster,
at the cost of test isolation.
