Name resolution
===============

Names in Nope are function-scoped, as in Python. That is, all identifiers with
the same name in the same function refer to the same variable.

Exception handler targets
-------------------------

Consider the following code:

.. code-block:: python

    try:
        assert False
    except Exception as error:
        print(error)
    
    print(error)

Since names are function-scoped, you might expect the code to be valid
(assuming it type-checks). However, due to the behaviour of exception handlers
in Python, this is not the case. Specifically, there's an implicit ``del``
statement at the end of each exception handler that deletes the exception
handler target. In other words, to make the implicit explicit:

.. code-block:: python

    try:
        assert False
    except Exception as error:
        print(error)
        del error
    
    print(error)

As a result, the second call ``print(error)`` fails since ``error`` is no longer bound.
Therefore, the Nope compiler would reject the above code.

This also means
that nested functions cannot refer to ``error``. This prevents a potentially
unbound identifier from escaping the exception handler. For instance, the following
code would cause an exception in Python, and is rejected by the Nope
compiler:

.. code-block:: python

    try:
        assert False
    except Exception as error:
        def f():
            print(error)
    
    f()

However, the following is valid:

.. code-block:: python

    try:
        assert False
    except Exception as error:
        saved_error = error
        def f():
            print(saved_error)

    f()

(Since this behaviour arises because of the implicit ``del``, the same
strategy should work if and when statements of the form ``del identifier`` are
supported.)
