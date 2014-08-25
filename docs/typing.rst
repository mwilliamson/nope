Typing
======

Expressions
-----------

Identifiers (Names)
~~~~~~~~~~~~~~~~~~~

The type of an identifier is the type associated with that identifier in
the context of the current scope.

String literals
~~~~~~~~~~~~~~~

All string literals have the type ``str``.

Integer literals
~~~~~~~~~~~~~~~~

All integer literals have the type ``int``.

List literals
~~~~~~~~~~~~~

An empty list literal has the type ``list[bottom]``.

A non-empty list literal has the type ``list[T]``, where ``T`` is the
unification of the types of the elements of the list.

Statements
----------
