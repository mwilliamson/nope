import ast
import tokenize
import io
import collections
import re

from . import transform, nodes


def parse(source):
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    comment_seeker = CommentSeeker(tokens)
    python_ast = ast.parse(source)
    
    return transform.python_to_nope(python_ast, comment_seeker)


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
                self._previous_tokens.append((token_type, token_str))
            
            if self._has_signature_comment():
                return _parse_signature(self._previous_tokens[0][1][len(self._comment_prefix):].strip())
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


def _parse_signature(sig_str):
    result = re.match("^([a-zA-Z0-9_]+)?\s*->\s*([a-zA-Z0-9_]+)$", sig_str)
    arg_annotations = [nodes.ref(result.group(1))]
    return_annotation = nodes.ref(result.group(2))
    return (arg_annotations, return_annotation)
