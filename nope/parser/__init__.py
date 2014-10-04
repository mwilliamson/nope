import ast
import io

from . import transform
from .typing import parse_signatures


def parse(source, filename=None):
    try:
        signatures = parse_signatures(io.StringIO(source))
        comment_seeker = CommentSeeker(signatures)
        python_ast = ast.parse(source)
        is_executable = source.startswith("#!/")
        nope_node = transform.python_to_nope(python_ast, comment_seeker, is_executable=is_executable, filename=filename)
        if signatures:
            error = SyntaxError("type signature is not valid here")
            (error.lineno, error.offset), _ = next(iter(signatures.values()))
            raise error
        return nope_node
    except SyntaxError as error:
        error.filename = filename
        raise error


class CommentSeeker(object):
    def __init__(self, signatures):
        self._signatures = signatures

    def consume_signature(self, lineno, col_offset):
        return self._signatures.pop((lineno, col_offset), (None, None))[1]
