import ast
import tokenize
import token
import io
import collections

from . import transform
from .typing import parse_signature


def parse(source, filename=None):
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        comment_seeker = CommentSeeker(tokens)
        python_ast = ast.parse(source)
        is_executable = source.startswith("#!/")
        return transform.python_to_nope(python_ast, comment_seeker, is_executable=is_executable, filename=filename)
    except SyntaxError as error:
        error.filename = filename
        raise error


class CommentSeeker(object):
    _comment_prefix = "#::"
    
    def __init__(self, tokens):
        self._tokens = tokens
        self._position = None
        self._previous_tokens = collections.deque(maxlen=3)

    def seek_signature(self, lineno, col_offset):
        try:
            while self._position != (lineno, col_offset):
                token_type, token_str, self._position, end_position, _ = next(self._tokens)
                
                if token_type != token.INDENT:
                    self._previous_tokens.append((token_type, token_str))
            
            if self._has_signature_comment():
                return parse_signature(self._previous_tokens[0][1][len(self._comment_prefix):].strip())
            else:
                return None
        except StopIteration:
            return None
    
    def _has_signature_comment(self):
        return (
            len(self._previous_tokens) == 3 and
            self._previous_tokens[0][0] == tokenize.COMMENT and
            self._previous_tokens[1][0] == tokenize.NL and
            self._previous_tokens[0][1].startswith(self._comment_prefix)
        )
