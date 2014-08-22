from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import update_context
from nope.context import bound_context

from .util import (
    assert_variable_remains_unbound,
    assert_statement_is_type_checked)


@istest
def if_statement_has_condition_type_checked():
    ref_node = nodes.ref("y")
    node = nodes.if_else(ref_node, [], [])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def if_statement_has_true_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.if_else(
            nodes.int(1),
            [bad_statement],
            [],
        )
    )


@istest
def if_statement_has_false_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.if_else(
            nodes.int(1),
            [],
            [bad_statement],
        )
    )


@istest
def assignment_in_both_branches_of_if_statement_is_added_to_context():
    node = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(1))],
        [nodes.assign("x", nodes.int(2))],
    )
    context = bound_context({"x": None})
    update_context(node, context)
    assert_equal(types.int_type, context.lookup("x"))


@istest
def type_of_variable_is_unified_if_branches_of_if_else_use_different_types():
    node = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(1))],
        [nodes.assign("x", nodes.string("blah"))],
    )
    context = bound_context({"x": None})
    update_context(node, context)
    assert_equal(types.object_type, context.lookup("x"))


@istest
def variable_remains_unbound_if_only_set_in_one_branch_of_if_else():
    assert_variable_remains_unbound(lambda assignment: nodes.if_else(
        nodes.int(1),
        [assignment],
        [],
    ))
