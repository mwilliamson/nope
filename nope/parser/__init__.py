import ast
import io

from . import transform
from .typing import parse_type_comments


def parse(source, filename=None):
    try:
        explicit_types, type_statements = parse_type_comments(io.StringIO(source))
        comment_seeker = CommentSeeker(explicit_types, type_statements)
        
        python_ast = ast.parse(source)
        is_executable = source.startswith("#!/")
        nope_node = transform.python_to_nope(python_ast, comment_seeker, is_executable=is_executable, filename=filename)
        if explicit_types:
            error = SyntaxError("explicit type is not valid here")
            (error.lineno, error.offset), _ = next(iter(explicit_types.values()))
            raise error
        return nope_node
    except SyntaxError as error:
        error.filename = filename
        raise error


class CommentSeeker(object):
    def __init__(self, explicit_types, type_statements):
        self._explicit_types = explicit_types
        self._type_statements = type_statements
    
    def consume_explicit_type(self, lineno, col_offset):
        return self._explicit_types.pop((lineno, col_offset), (None, None))[1]
    
    def consume_type_definition(self, lineno, col_offset):
        return self._type_statements.pop((lineno, col_offset), (None, None))[1]
