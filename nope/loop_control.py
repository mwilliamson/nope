from . import structure, nodes, errors
from .dispatch import TypeDispatch


def check_loop_control(node, in_loop, in_finally=False):
    return _check_loop_control(node, in_loop, in_finally)


def _check_children(node, in_loop, in_finally):
    for child in structure.children(node):
        _check_loop_control(child, in_loop, in_finally)


def _check_loop(node, in_loop, in_finally):
    _check_loop_body(node.body)
    _check_statements(node.else_body, in_loop, in_finally)


def _check_loop_body(statements):
    for statement in statements:
        _check_loop_control(statement, True, False)


def _check_statements(statements, in_loop, in_finally):
    for statement in statements:
        _check_loop_control(statement, in_loop, in_finally)


def _check_break(node, in_loop, in_finally):
    _assert_in_loop(node, in_loop, "break")


def _check_continue(node, in_loop, in_finally):
    if in_finally:
        raise errors.InvalidStatementError(node, "'continue' not supported inside 'finally' clause")
    _assert_in_loop(node, in_loop, "continue")


def _assert_in_loop(node, in_loop, name):
    if not in_loop:
        raise errors.InvalidStatementError(node, "'{}' outside loop".format(name))


def _check_try(node, in_loop, in_finally):
    _check_statements(node.body, in_loop, in_finally)
    for handler in node.handlers:
        _check_statements(handler.body, in_loop, in_finally)
    _check_statements(node.finally_body, in_loop, True)


def _check_function_definition(node, in_loop, in_finally):
    _check_statements(node.body, False, False)


def _check_class_definition(node, in_loop, in_finally):
    _check_statements(node.body, False, False)


_check_loop_control = TypeDispatch({
    nodes.WhileLoop: _check_loop,
    nodes.ForLoop: _check_loop,
    nodes.BreakStatement: _check_break,
    nodes.ContinueStatement: _check_continue,
    nodes.TryStatement: _check_try,
    nodes.FunctionDef: _check_function_definition,
    nodes.ClassDefinition: _check_class_definition,
}, default=_check_children)
