from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.identity_dict import NodeDict

from .util import update_context


@istest
def function_definitions_in_statement_lists_can_be_defined_out_of_order():
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(nodes.ref("g"), []))
    ])
    g = nodes.func("g", type=None, args=nodes.Arguments([]), body=[])
    _update_context([f, g, nodes.expression_statement(nodes.ref("f"))])


@istest
def function_definitions_in_statement_lists_can_be_mutually_recursive():
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(nodes.ref("g"), []))
    ])
    g = nodes.func("g", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(nodes.ref("f"), []))
    ])
    _update_context([f, g])


@istest
def function_definitions_in_statement_lists_are_type_checked_even_if_not_invoked():
    node = nodes.func("f", type=None, args=nodes.Arguments([]), body=[nodes.ret(nodes.int_literal(42))])
    try:
        _update_context([node])
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(types.int_type, error.actual)
        assert_equal(types.none_type, error.expected)


@istest
def attributes_assigned_in_init_can_be_used_outside_of_class():
    init_func = nodes.func(
        name="__init__",
        args=nodes.args([nodes.arg("self_init")]),
        body=[
            nodes.assign(
                [nodes.attr(nodes.ref("self_init"), "message")],
                nodes.str_literal("Hello")
            )
        ],
        type=nodes.signature(
            args=[nodes.signature_arg(nodes.ref("Self"))],
            returns=nodes.ref("none")
        )
    )
    class_node = nodes.class_("User", [init_func])
    
    node = [
        class_node,
        nodes.assign([nodes.ref("x")], nodes.attr(nodes.call(nodes.ref("User"), []), "message")),
    ]
    
    context = _update_context(node, declared_names_in_node=NodeDict([
        (class_node, ["Self", "__init__"]),
        (init_func, ["self_init"]),
    ]))
    
    assert_equal(types.str_type, context.lookup_name("x"))


def _update_context(func_node, *, type_bindings=None, declared_names_in_node=None):
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
    
    return update_context(func_node, type_bindings=type_bindings, declared_names_in_node=declared_names_in_node)
