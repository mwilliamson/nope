from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import update_context
from nope.context import bound_context

from .util import (
    assert_type_mismatch,
    assert_statement_type_checks,
    assert_statement_is_type_checked,
    assert_expression_is_type_checked)


@istest
def body_of_with_expression_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.with_statement(nodes.ref("x"), None, [
            bad_statement
        ]),
        bound_context({
            "x": _context_manager_class(),
        })
    )


@istest
def context_manager_of_with_statement_is_type_checked():
    assert_expression_is_type_checked(
        lambda bad_expr: nodes.with_statement(bad_expr, None, []),
    )


@istest
def context_manager_of_with_statement_must_have_enter_method():
    cls = types.scalar_type("Manager", [types.attr("__exit__", _exit_method())])
    context_manager_node = nodes.ref("x")
    node = nodes.with_statement(context_manager_node, None, [])
    
    context = bound_context({"x": cls})
    assert_type_mismatch(
        lambda: update_context(node, context),
        expected="object with method '__enter__'",
        actual=cls,
        node=context_manager_node,
    )


@istest
def context_manager_of_with_statement_must_have_exit_method():
    cls = types.scalar_type("Manager", [types.attr("__enter__", _enter_method())])
    context_manager_node = nodes.ref("x")
    node = nodes.with_statement(context_manager_node, None, [])
    
    context = bound_context({"x": cls})
    assert_type_mismatch(
        lambda: update_context(node, context),
        expected="object with method '__exit__'",
        actual=cls,
        node=context_manager_node,
    )


@istest
def target_can_be_supertype_of_return_type_of_enter_method():
    node = nodes.with_statement(nodes.ref("x"), nodes.ref("y"), [])
    
    context = bound_context({"x": _context_manager_class(types.int_type), "y": types.any_type})
    assert_statement_type_checks(node, context)


@istest
def target_cannot_be_strict_subtype_of_return_type_of_enter_method():
    target_node = nodes.ref("y")
    node = nodes.with_statement(nodes.ref("x"), target_node, [])
    
    context = bound_context({"x": _context_manager_class(types.any_type), "y": types.int_type})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.BadAssignmentError as error:
        assert_equal(target_node, error.node)
        assert_equal(types.any_type, error.value_type)
        assert_equal(types.int_type, error.target_type)


@istest
def assigned_variables_in_with_statement_body_are_still_bound_after_exit_if_exit_method_always_returns_none():
    node = nodes.with_statement(nodes.ref("x"), None, [
        nodes.assign(nodes.ref("z"), nodes.none()),
    ])
    
    context = bound_context({
        "x": _context_manager_class(exit_type=types.none_type),
        "z": None,
    })
    update_context(node, context)
    assert_equal(types.none_type, context.lookup("z"))


@istest
def assigned_variables_in_with_statement_body_are_unbound_after_exit_if_exit_method_does_not_return_none():
    node = nodes.with_statement(nodes.ref("x"), None, [
        nodes.assign(nodes.ref("z"), nodes.none()),
    ])
    
    context = bound_context({
        "x": _context_manager_class(exit_type=types.any_type),
        "z": None,
    })
    update_context(node, context)
    assert not context.is_bound("z")
    assert_equal(types.none_type, context.lookup("z", allow_unbound=True))


def _context_manager_class(enter_type=None, exit_type=None):
    return types.scalar_type("Manager", [
        types.attr("__enter__", _enter_method(enter_type), read_only=True),
        types.attr("__exit__", _exit_method(exit_type), read_only=True),
    ])


def _enter_method(return_type=None):
    if return_type is None:
        return_type = types.none_type
    return types.func([], return_type)


def _exit_method(return_type=None):
    if return_type is None:
        return_type = types.none_type
    return types.func([types.exception_meta_type, types.exception_type, types.traceback_type], return_type)
