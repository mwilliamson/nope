import ast
import io

from . import transform
from .typing import parse_type_comments


def parse(source, filename=None):
    try:
        type_comments = parse_type_comments(io.StringIO(source))
        comment_seeker = CommentSeeker(type_comments)
        
        python_ast = ast.parse(source)
        is_executable = source.startswith("#!/")
        nope_node = transform.python_to_nope(python_ast, comment_seeker, is_executable=is_executable, filename=filename)
        if type_comments.explicit_types:
            error = SyntaxError("explicit type is not valid here")
            (error.lineno, error.offset), _ = next(iter(type_comments.explicit_types.values()))
            raise error
        return nope_node
    except SyntaxError as error:
        error.filename = filename
        raise error


class CommentSeeker(object):
    def __init__(self, type_comments):
        self._explicit_types = type_comments.explicit_types
        self._type_definitions = type_comments.type_definitions
        self._generics = type_comments.generics
    
    def consume_explicit_type(self, lineno, col_offset):
        return self._consume(self._explicit_types, lineno, col_offset)
        return self._explicit_types.pop((lineno, col_offset), (None, None))[1]
    
    def consume_type_definition(self, lineno, col_offset):
        return self._consume(self._type_definitions, lineno, col_offset)
    
    def consume_generic(self, lineno, col_offset):
        return self._consume(self._generics, lineno, col_offset)
    
    def _consume(self, values, lineno, col_offset):
        return values.pop((lineno, col_offset), (None, None))[1]
