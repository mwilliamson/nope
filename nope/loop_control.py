from . import visit, nodes, errors


def check_loop_control(node, in_loop, in_finally=False):
    visitor = visit.Visitor()
    visitor.replace(nodes.WhileLoop, _check_loop)
    visitor.replace(nodes.ForLoop, _check_loop)
    visitor.before(nodes.BreakStatement, _check_break)
    visitor.before(nodes.ContinueStatement, _check_continue)
    visitor.replace(nodes.TryStatement, _check_try)
    visitor.replace(nodes.FunctionDef, _check_function_definition)
    visitor.replace(nodes.ClassDefinition, _check_class_definition)
    
    visitor.visit(node, in_loop, in_finally)


def _check_loop(visitor, node, in_loop, in_finally):
    _check_loop_body(visitor, node.body)
    _check_statements(visitor, node.else_body, in_loop, in_finally)


def _check_loop_body(visitor, statements):
    for statement in statements:
        visitor.visit(statement, True, False)


def _check_statements(visitor, statements, in_loop, in_finally):
    for statement in statements:
        visitor.visit(statement, in_loop, in_finally)


def _check_break(visitor, node, in_loop, in_finally):
    _check_loop_control(node, in_loop, in_finally, "break")


def _check_continue(visitor, node, in_loop, in_finally):
    if in_finally:
        raise errors.InvalidStatementError(node, "'continue' not supported inside 'finally' clause")
    _check_loop_control(node, in_loop, in_finally, "continue")


def _check_loop_control(node, in_loop, in_finally, name):
    if not in_loop:
        raise errors.InvalidStatementError(node, "'{}' outside loop".format(name))


def _check_try(visitor, node, in_loop, in_finally):
    _check_statements(visitor, node.body, in_loop, in_finally)
    for handler in node.handlers:
        _check_statements(visitor, handler.body, in_loop, in_finally)
    _check_statements(visitor, node.finally_body, in_loop, True)


def _check_function_definition(visitor, node, in_loop, in_finally):
    _check_statements(visitor, node.body, False, False)


def _check_class_definition(visitor, node, in_loop, in_finally):
    _check_statements(visitor, node.body, False, False)
