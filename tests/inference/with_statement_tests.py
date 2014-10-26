from nose.tools import istest, assert_equal

from nope import types, nodes, errors

from .util import (
    assert_statement_type_checks,
    assert_statement_is_type_checked,
    assert_expression_is_type_checked,
    update_context,
    context_manager_class, enter_method, exit_method)


@istest
def body_of_with_expression_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.with_statement(nodes.ref("x"), None, [
            bad_statement
        ]),
        type_bindings={
            "x": context_manager_class(),
        }
    )


@istest
def context_manager_of_with_statement_is_type_checked():
    assert_expression_is_type_checked(
        lambda bad_expr: nodes.with_statement(bad_expr, None, []),
    )


@istest
def context_manager_of_with_statement_must_have_enter_method():
    cls = types.scalar_type("Manager", [types.attr("__exit__", exit_method())])
    context_manager_node = nodes.ref("x")
    node = nodes.with_statement(context_manager_node, None, [])
    
    try:
        update_context(node, type_bindings={"x": cls})
        assert False, "Expected error"
    except errors.NoSuchAttributeError as error:
        assert_equal(nodes.attr(context_manager_node, "__enter__"), error.node)


@istest
def context_manager_of_with_statement_must_have_exit_method():
    cls = types.scalar_type("Manager", [types.attr("__enter__", enter_method())])
    context_manager_node = nodes.ref("x")
    node = nodes.with_statement(context_manager_node, None, [])
    
    try:
        update_context(node, type_bindings={"x": cls})
        assert False, "Expected error"
    except errors.NoSuchAttributeError as error:
        assert_equal(nodes.attr(context_manager_node, "__exit__"), error.node)


@istest
def target_can_be_supertype_of_return_type_of_enter_method():
    node = nodes.with_statement(nodes.ref("x"), nodes.ref("y"), [])
    
    type_bindings = {"x": context_manager_class(types.int_type), "y": types.any_type}
    assert_statement_type_checks(node, type_bindings=type_bindings)


@istest
def target_cannot_be_strict_subtype_of_return_type_of_enter_method():
    target_node = nodes.ref("y")
    node = nodes.with_statement(nodes.ref("x"), target_node, [])
    
    type_bindings = {"x": context_manager_class(types.any_type), "y": types.int_type}
    try:
        update_context(node, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnexpectedTargetTypeError as error:
        assert_equal(target_node, error.node)
        assert_equal(types.any_type, error.value_type)
        assert_equal(types.int_type, error.target_type)
