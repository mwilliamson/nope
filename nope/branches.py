from . import types



def if_else(statement, before_true=None, before_false=None):
    return _Branches(
        [
            _Branch(statement.true_body, before=before_true),
            _Branch(statement.false_body, before=before_false)
        ],
        conditional=False,
    )


def while_loop(statement):
    return _Branches(
        [_Branch(statement.body), _Branch(statement.else_body)],
        conditional=True,
    )


def for_loop(statement, target):
    return _Branches(
        [
            _Branch(statement.body, before=target),
            _Branch(statement.else_body)
        ],
        conditional=True,
    )


def try_statement(statement, before_handler, after_handler=None):
    branches = []
    
    branches.append(_Branch(statement.body))
    for handler in statement.handlers:
        branches.append(_create_handler_branch(handler, before_handler, after_handler))
    branches.append(_Branch(statement.finally_body))
    
    return _Branches(
        branches,
        conditional=True,
    )
    
def _create_handler_branch(handler, before_handler, after_handler):
    def bind_handler_func(func):
        if func is None:
            return None
        else:
            return lambda context: func(handler, context)
    
    return _Branch(
        handler.body,
        before=bind_handler_func(before_handler),
        after=bind_handler_func(after_handler),
    )


def with_statement(statement, before, exit_return_type):
    return _Branches(
        [_Branch(statement.body, before=before)],
        conditional=exit_return_type != types.none_type,
    )


class _Branches(object):
    def __init__(self, branches, conditional):
        self.branches = branches
        self.conditional = conditional


class _Branch(object):
    def __init__(self, statements, before=None, after=None):
        self.statements = statements
        self.before = before
        self.after = after
