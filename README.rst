The Nope Programming Language
=============================

Nope is a subset of Python 3 that can be compiled to multiple targets.
At the moment, only Python and node.js are supported.
Any valid Nope program can be run directly as a Python 3 program.

Comments are used to provide static typing.
As well as detecting programming errors more quickly,
this allows translation to simpler code.

TODO
----

* When defining `__add__` and similar methods on classes,
  the type signature should be specific e.g. on int, `int -> int`.
  However, to maintain compatibility with Python,
  the type checker should assume the argument is the top type when type
  checking the actual method, so isinstance or similar still has to be used.

* Support for the r versions of operators e.g. `__radd__`.

* Class definitions

* Standard library support

* A way of specifying dependencies on a per-platform basis to allow shimming
  of existing libraries into a common interface.

Status
------

Syntax
~~~~~~

This section describes support for parsing and type-checking each of
`Python 3.4's syntax nodes <https://docs.python.org/3.4/library/ast.html#abstract-grammar>`_.

* **Function definitions**: partially supported.

  * **name**: supported.
  
  * **arguments**: partially supported.
    Positional arguments are supported, but nothing else
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

* **Class definitions**: unsupported.

* **Return statements**: supported.

* **Delete statements**: unsupported.

* **Assignments**: partially supported.
  Assignments to variables (e.g. ``x``) and elements of sequences (e.g. ``x[i]``)
  are supported, but not assignment to slices (e.g. ``x[:]``) nor attributes (e.g. ``x.y``)

* **Augmented assignments**: unsupported.

* **For loops**: partially supported.
  The sequence protocol is currently unsupported, as is the ``else`` block.
  
* **While loops**: unsupported.

* **If statements**: supported.

* **With statments**: unsupported.

* **Raise statements**: unsupported.

* **Try statements**: unsupported.

* **Assert statements**: unsupported.

* **Import statements**: partially supported.
  The various forms of import statement are supported.
  However, only local modules are currently supported.
  Modules from the standard library or dependencies are unsupported.
  
* **``global`` keyword**: unsupported.

* **``nonlocal`` keyword**: unsupported.

* **Expression statements**: supported.

* **``pass`` keyword**: supported.

* **``break`` keyword**: supported.

* **``continue`` keyword**: supported.
