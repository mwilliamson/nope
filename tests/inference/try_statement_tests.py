from nose.tools import istest, assert_equal

from nope import types, nodes

from .util import (
    assert_type_mismatch, assert_variable_remains_unbound,
    assert_statement_is_type_checked, assert_variable_is_bound,
    update_context)


@istest
def try_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_statement([bad_statement])
    )


@istest
def except_handler_type_must_be_type():
    type_node = nodes.ref("x")
    node = nodes.try_statement([], handlers=[
        nodes.except_handler(type_node, None, []),
    ])
    assert_type_mismatch(
        lambda: update_context(node, type_bindings={"x": types.int_type}),
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
    assert_type_mismatch(
        lambda: update_context(node, type_bindings={"int": meta_type}),
        expected="exception type",
        actual=meta_type,
        node=type_node,
    )


@istest
def except_handler_updates_type_of_error_target():
    node = nodes.try_statement([], handlers=[
        nodes.except_handler(
            nodes.ref("Exception"),
            "error",
            [nodes.expression_statement(nodes.ref("error"))]
        ),
    ])
    type_bindings = {
        "Exception": types.meta_type(types.exception_type)
    }
    context = update_context(node, type_bindings=type_bindings)
    assert_equal(types.exception_type, context.lookup_name("error"))


@istest
def try_except_handler_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_statement([], handlers=[
            nodes.except_handler(None, None, [bad_statement]),
        ])
    )


@istest
def try_finally_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_statement([], finally_body=[bad_statement])
    )
