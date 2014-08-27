from nose.tools import istest, assert_equal

from nope import types, nodes, errors

from .util import (
    assert_type_mismatch,
    assert_statement_type_checks,
    assert_statement_is_type_checked,
    assert_expression_is_type_checked,
    update_context,
    create_context,
    context_manager_class, enter_method, exit_method)


@istest
def body_of_with_expression_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.with_statement(nodes.ref("x"), None, [
            bad_statement
        ]),
        create_context({
            "x": context_manager_class(),
        })
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
    
    context = create_context({"x": cls})
    assert_type_mismatch(
        lambda: update_context(node, context),
        expected="object with method '__enter__'",
        actual=cls,
        node=context_manager_node,
    )


@istest
def context_manager_of_with_statement_must_have_exit_method():
    cls = types.scalar_type("Manager", [types.attr("__enter__", enter_method())])
    context_manager_node = nodes.ref("x")
    node = nodes.with_statement(context_manager_node, None, [])
    
    context = create_context({"x": cls})
    assert_type_mismatch(
        lambda: update_context(node, context),
        expected="object with method '__exit__'",
        actual=cls,
        node=context_manager_node,
    )


@istest
def target_can_be_supertype_of_return_type_of_enter_method():
    node = nodes.with_statement(nodes.ref("x"), nodes.ref("y"), [])
    
    context = create_context({"x": context_manager_class(types.int_type), "y": types.any_type})
    assert_statement_type_checks(node, context)


@istest
def target_cannot_be_strict_subtype_of_return_type_of_enter_method():
    target_node = nodes.ref("y")
    node = nodes.with_statement(nodes.ref("x"), target_node, [])
    
    context = create_context({"x": context_manager_class(types.any_type), "y": types.int_type})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.BadAssignmentError as error:
        assert_equal(target_node, error.node)
        assert_equal(types.any_type, error.value_type)
        assert_equal(types.int_type, error.target_type)
