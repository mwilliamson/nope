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
