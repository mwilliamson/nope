from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import update_context
from nope.context import bound_context

from .util import assert_statement_is_type_checked



@istest
def while_loop_has_condition_type_checked():
    condition_node = nodes.ref("x")
    node = nodes.while_loop(condition_node, [])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(condition_node, error.node)


@istest
def while_loop_has_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement:
            nodes.while_loop(nodes.boolean(True), [bad_statement])
    )


@istest
def while_loop_has_else_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement:
            nodes.while_loop(nodes.boolean(True), [], [bad_statement])
    )


@istest
def type_of_variable_remains_undefined_if_set_in_while_loop_body():
    node = nodes.while_loop(nodes.boolean(True), [
        nodes.assign([nodes.ref("x")], nodes.int(2))
    ])
    context = bound_context({"x": None})
    update_context(node, context)
    assert not context.is_bound("x")
    assert_equal(types.int_type, context.lookup("x", allow_unbound=True))
