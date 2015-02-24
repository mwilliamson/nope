from nose.tools import istest, assert_equal

from nope import nodes, errors, types

from .util import assert_statement_is_type_checked, update_context



@istest
def while_loop_has_condition_type_checked():
    condition_node = nodes.ref("x")
    node = nodes.while_(condition_node, [])
    
    try:
        update_context(node)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(condition_node, error.node)


@istest
def while_loop_has_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement:
            nodes.while_(nodes.bool_literal(True), [bad_statement])
    )


@istest
def while_loop_has_else_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement:
            nodes.while_(nodes.bool_literal(True), [], [bad_statement])
    )


@istest
def after_while_loop_variables_could_have_previous_type_or_assigned_type():
    node = nodes.while_(nodes.bool_literal(True),
        [nodes.assign([nodes.ref("x")], nodes.none())],
        [nodes.assign([nodes.ref("x")], nodes.none())],
    )
    type_bindings = {"x": types.int_type}
    context = update_context(node, type_bindings=type_bindings)
    assert_equal(types.common_super_type([types.int_type, types.none_type]), context.lookup_name("x"))
