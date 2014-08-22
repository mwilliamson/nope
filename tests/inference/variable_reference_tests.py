from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import infer
from nope.context import bound_context


@istest
def can_infer_type_of_variable_reference():
    assert_equal(types.int_type, infer(nodes.ref("x"), bound_context({"x": types.int_type})))


@istest
def type_error_if_ref_to_undefined_variable():
    node = nodes.ref("x")
    try:
        infer(node, bound_context({}))
        assert False, "Expected error"
    except errors.UndefinedNameError as error:
        assert_equal(node, error.node)
        assert_equal("name 'x' is not defined", str(error))
