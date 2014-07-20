import ast

from . import transform


def parse(source):
    python_ast = ast.parse(source)
    
    return transform.python_to_nope(python_ast)
