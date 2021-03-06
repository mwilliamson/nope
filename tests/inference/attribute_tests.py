from nose.tools import istest, assert_equal

from nope import types, nodes, errors

from .util import infer


@istest
def can_infer_type_of_attribute():
    type_bindings = {"x": types.str_type}
    assert_equal(
        types.func([types.str_type], types.int_type),
        infer(nodes.attr(nodes.ref("x"), "find"), type_bindings=type_bindings)
    )


@istest
def type_error_if_attribute_does_not_exist():
    type_bindings = {"x": types.str_type}
    node = nodes.attr(nodes.ref("x"), "swizzlify")
    try:
        infer(node, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.NoSuchAttributeError as error:
        assert_equal("'str' object has no attribute 'swizzlify'", str(error))
        assert error.node is node
