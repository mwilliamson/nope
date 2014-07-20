import ast
import tokenize
import io
import collections

from funcparserlib.lexer import make_tokenizer
from funcparserlib.parser import (some, a, many, maybe, finished)

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


def _token_type(token_type):
    return some(lambda token: token.type == token_type)


def _make_type(result):
    return nodes.ref(result.value)


def _make_args(result):
    if result is None:
        return []
    else:
        return [result[0]] + [extra_arg[1] for extra_arg in result[1]]


def _make_signature(result):
    return result[0], result[2]


_type = _token_type("name") >> _make_type
_args = maybe(_type + many(_token_type("comma") + _type)) >> _make_args
_signature = (_args + _token_type("arrow") + _type + finished) >> _make_signature


def _parse_signature(sig_str):
    tokens = _tokenize_signature(sig_str)
    return _signature.parse(tokens)
    
    
def _tokenize_signature(sig_str):
    specs = [
        ('space', (r'[ \t]+', )),
        ('name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
        ('arrow', (r'->', )),
        ('comma', (r',', )),
    ]
    ignore = ['space']
    tokenizer = make_tokenizer(specs)
    return [token for token in tokenizer(sig_str) if token.type not in ignore]
