from nose.tools import istest

from nope import types, nodes
from nope.inference import update_context
from nope.context import bound_context

from .util import (
    assert_type_mismatch, assert_variable_remains_unbound,
    assert_statement_is_type_checked, assert_variable_is_bound)


@istest
def try_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_statement([bad_statement])
    )


@istest
def assigned_variable_in_try_body_remains_unbound():
    assert_variable_remains_unbound(
        lambda assignment: nodes.try_statement([assignment])
    )


@istest
def except_handler_type_must_be_type():
    type_node = nodes.ref("x")
    node = nodes.try_statement([], handlers=[
        nodes.except_handler(type_node, None, []),
    ])
    context = bound_context({"x": types.int_type})
    assert_type_mismatch(
        lambda: update_context(node, context),
        expected="exception type",
        actual=types.int_type,
        node=type_node,
    )


@istest
def except_handler_type_must_be_exception_type():
    type_node = nodes.ref("int")
    node = nodes.try_statement([], handlers=[
        nodes.except_handler(type_node, None, []),
    ])
    meta_type = types.meta_type(types.int_type)
    context = bound_context({"int": meta_type})
    assert_type_mismatch(
        lambda: update_context(node, context),
        expected="exception type",
        actual=meta_type,
        node=type_node,
    )


@istest
def except_handler_binds_error_name_in_handler_body_only():
    node = nodes.try_statement([], handlers=[
        nodes.except_handler(
            nodes.ref("Exception"),
            "error",
            [nodes.expression_statement(nodes.ref("error"))]
        ),
    ])
    context = bound_context({
        "error": None,
        "Exception": types.meta_type(types.exception_type)
    })
    update_context(node, context)
    # Make sure the name is unbound afterwards
    assert not context.is_bound("error")


@istest
def try_except_handler_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_statement([], handlers=[
            nodes.except_handler(None, None, [bad_statement]),
        ])
    )


@istest
def assigned_variable_in_try_except_handler_body_remains_unbound():
    assert_variable_remains_unbound(
        lambda assignment: nodes.try_statement([], handlers=[
            nodes.except_handler(None, None, [assignment]),
        ])
    )


@istest
def try_finally_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_statement([], finally_body=[bad_statement])
    )


@istest
def assigned_variable_in_finally_body_is_bound():
    assert_variable_is_bound(
        lambda assignment: nodes.try_statement([], finally_body=[assignment])
    )
