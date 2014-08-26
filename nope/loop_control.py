from . import visit, nodes, errors


def check_loop_control(node, in_loop):
    visitor = visit.Visitor()
    visitor.replace(nodes.WhileLoop, _check_loop)
    visitor.replace(nodes.ForLoop, _check_loop)
    visitor.before(nodes.BreakStatement, _check_break)
    visitor.before(nodes.ContinueStatement, _check_continue)
    visitor.replace(nodes.FunctionDef, _check_function_definition)
    
    visitor.visit(node, in_loop)


def _check_loop(visitor, node, in_loop):
    _check_loop_body(visitor, node.body)
    _check_statements(visitor, node.else_body, in_loop)


def _check_loop_body(visitor, statements):
    for statement in statements:
        visitor.visit(statement, True)


def _check_statements(visitor, statements, in_loop):
    for statement in statements:
        visitor.visit(statement, in_loop)


def _check_break(visitor, node, in_loop):
    _check_loop_control(node, in_loop, "break")


def _check_continue(visitor, node, in_loop):
    _check_loop_control(node, in_loop, "continue")


def _check_loop_control(node, in_loop, name):
    if not in_loop:
        raise errors.InvalidStatementError(node, "'{}' outside loop".format(name))


def _check_function_definition(visitor, node, in_loop):
    _check_statements(visitor, node.body, False)
