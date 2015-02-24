from nose.tools import istest

from nope import nodes

from .util import assert_expression_is_type_checked


@istest
def assert_condition_is_type_checked():
    assert_expression_is_type_checked(
        lambda bad_expr: nodes.assert_(bad_expr)
    )


@istest
def assert_message_is_type_checked():
    assert_expression_is_type_checked(
        lambda bad_expr: nodes.assert_(nodes.bool_literal(False), bad_expr)
    )
