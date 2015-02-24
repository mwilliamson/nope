from nose.tools import istest

from nope import returns, nodes


@istest
def has_unconditional_return_is_false_for_empty_list():
    assert not returns.has_unconditional_return([])


@istest
def has_unconditional_return_is_true_if_list_contains_a_return_statement():
    assert returns.has_unconditional_return([
        nodes.ret(nodes.int_literal(1))
    ])


@istest
def has_unconditional_return_is_true_if_both_branches_of_if_statement_return():
    assert returns.has_unconditional_return([
        nodes.if_(
            nodes.int_literal(1),
            [nodes.ret(nodes.int_literal(1))],
            [nodes.ret(nodes.int_literal(2))],
        )
    ])


@istest
def has_unconditional_return_is_false_if_only_true_branch_of_if_statement_returns():
    assert not returns.has_unconditional_return([
        nodes.if_(
            nodes.int_literal(1),
            [nodes.ret(nodes.int_literal(1))],
            [],
        )
    ])


@istest
def has_unconditional_return_is_false_if_only_false_branch_of_if_statement_returns():
    assert not returns.has_unconditional_return([
        nodes.if_(
            nodes.int_literal(1),
            [],
            [nodes.ret(nodes.int_literal(2))],
        )
    ])
