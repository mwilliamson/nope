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
