from nose.tools import istest, assert_equal

from nope import types, nodes

from .util import (
    assert_type_mismatch,
    assert_statement_is_type_checked,
    update_context)


@istest
def try_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_([bad_statement])
    )


@istest
def except_handler_type_must_be_type():
    type_node = nodes.ref("x")
    node = nodes.try_([], handlers=[
        nodes.except_(type_node, None, []),
    ])
    assert_type_mismatch(
        lambda: update_context(node, type_bindings={"x": types.int_type}),
        expected="type",
        actual=types.int_type,
        node=type_node,
    )


@istest
def except_handler_type_must_be_exception_type():
    type_node = nodes.ref("int")
    node = nodes.try_([], handlers=[
        nodes.except_(type_node, None, []),
    ])
    assert_type_mismatch(
        lambda: update_context(node, type_bindings={"int": types.int_meta_type}),
        expected="exception type",
        actual=types.int_meta_type,
        node=type_node,
    )


@istest
def except_handler_updates_type_of_error_target():
    node = nodes.try_([], handlers=[
        nodes.except_(
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
        lambda bad_statement: nodes.try_([], handlers=[
            nodes.except_(None, None, [bad_statement]),
        ])
    )


@istest
def try_finally_body_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.try_([], finally_body=[bad_statement])
    )
