from . import nodes


def has_unconditional_return(statements):
    for statement in statements:
        if isinstance(statement, (nodes.ReturnStatement, nodes.RaiseStatement)):
            return True
        elif isinstance(statement, nodes.IfElse):
            if has_unconditional_return(statement.true_body) and has_unconditional_return(statement.false_body):
                return True
    
    return False
