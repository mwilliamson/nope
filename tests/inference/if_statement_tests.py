from nose.tools import istest, assert_equal

from nope import types, nodes, errors, inference, builtins, name_declaration
from nope.name_resolution import References

from .util import (
    assert_statement_is_type_checked,
    update_context)


@istest
def if_statement_has_condition_type_checked():
    ref_node = nodes.ref("y")
    node = nodes.if_(ref_node, [], [])
    
    try:
        update_context(node)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def if_statement_has_true_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.if_(
            nodes.int_literal(1),
            [bad_statement],
            [],
        )
    )


@istest
def if_statement_has_false_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.if_(
            nodes.int_literal(1),
            [],
            [bad_statement],
        )
    )
