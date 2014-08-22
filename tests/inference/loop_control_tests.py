from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import update_context
from nope.context import bound_context


@istest
def break_is_not_valid_in_module():
    node = nodes.break_statement()
    context = bound_context({})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_valid_in_for_loop():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [nodes.break_statement()])
    context = bound_context({"x": types.int_type, "xs": types.list_type(types.int_type)})
    update_context(node, context)


@istest
def break_is_valid_in_if_else_in_for_loop():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [
        nodes.if_else(nodes.ref("x"), [nodes.break_statement()], []),
    ])
    context = bound_context({"x": types.int_type, "xs": types.list_type(types.int_type)})
    update_context(node, context)


@istest
def continue_is_not_valid_in_module():
    node = nodes.continue_statement()
    context = bound_context({})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'continue' outside loop", str(error))
