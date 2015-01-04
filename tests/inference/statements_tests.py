from nose.tools import istest, assert_equal, assert_is

from nope import types, nodes, errors

from .util import assert_type_mismatch, update_context


@istest
def function_definitions_in_statement_lists_can_be_defined_out_of_order():
    f = nodes.func("f", args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(nodes.ref("g"), []))
    ])
    g = nodes.func("g", args=nodes.Arguments([]), body=[])
    _update_context([f, g])


@istest
def function_definitions_in_statement_lists_are_type_checked_even_if_not_invoked():
    node = nodes.func("f", args=nodes.Arguments([]), body=[nodes.ret(nodes.int_literal(42))])
    try:
        context = _update_context([node])
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(types.int_type, error.actual)
        assert_equal(types.none_type, error.expected)


def _update_context(func_node, type_bindings=None):
    if type_bindings is None:
        type_bindings = {}
    else:
        type_bindings = type_bindings.copy()
    
    type_bindings.update({
        "int": types.meta_type(types.int_type),
        "str": types.meta_type(types.str_type),
        "none": types.meta_type(types.none_type),
        "list": types.meta_type(types.list_type),
    })
    
    return update_context(func_node, type_bindings=type_bindings)
