from nose.tools import istest, assert_equal

from nope import types, nodes, errors

from .util import infer, create_context


@istest
def can_infer_type_of_variable_reference():
    assert_equal(types.int_type, infer(nodes.ref("x"), create_context({"x": types.int_type})))


@istest
def type_error_if_ref_to_undefined_variable():
    node = nodes.ref("x")
    try:
        infer(node, create_context({}))
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(node, error.node)
        assert_equal("local variable x referenced before assignment", str(error))
