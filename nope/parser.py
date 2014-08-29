import ast
import tokenize
import token
import io
import collections

from funcparserlib.lexer import make_tokenizer
from funcparserlib.parser import (some, many, maybe, finished, forward_decl, skip)

from . import transform, nodes


def parse(source, filename=None):
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        comment_seeker = CommentSeeker(tokens)
        python_ast = ast.parse(source)
        is_executable = source.startswith("#!/")
        return transform.python_to_nope(python_ast, comment_seeker, is_executable=is_executable, filename=filename)
    except SyntaxError as error:
        if error.filename is None:
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


def _token_type(token_type):
    return some(lambda token: token.type == token_type)


def _make_name(result):
    return result.value


def _make_type(result):
    return nodes.ref(result)


def _make_apply(result):
    extra_params = [param[1] for param in result[3]]
    return nodes.type_apply(result[0], [result[2]] + extra_params)


def _make_params(result):
    if result is None:
        return result
    else:
        return [result[0]]


def _make_arg(result):
    return nodes.signature_arg(result[0], result[1])
    

def _make_args(result):
    if result is None:
        return []
    else:
        return [result[0]] + [extra_arg[1] for extra_arg in result[1]]


def _make_signature(result):
    return nodes.signature(
        type_params=result[0],
        args=result[1],
        returns=result[3],
    )
    


def _create_signature_rule():
    comma = _token_type("comma")
    colon = _token_type("colon")
    type_name = arg_name = _token_type("name") >> _make_name

    type_ = forward_decl()
    type_ref = type_name >> _make_type
    applied_type = (type_ref + _token_type("open") + type_ + many(comma + type_) + _token_type("close")) >> _make_apply
    type_.define(applied_type | type_ref)
    
    arg = (maybe(arg_name + skip(colon)) + type_) >> _make_arg
    
    generic_params = maybe(type_name + _token_type("fat-arrow")) >> _make_params
    args = maybe(arg + many(comma + arg)) >> _make_args
    return (generic_params + args + _token_type("arrow") + type_ + finished) >> _make_signature


_signature = _create_signature_rule()


def parse_signature(sig_str):
    tokens = _tokenize_signature(sig_str)
    return _signature.parse(tokens)
    
    
def _tokenize_signature(sig_str):
    specs = [
        ('space', (r'[ \t]+', )),
        ('name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
        ('fat-arrow', (r'=>', )),
        ('arrow', (r'->', )),
        ('comma', (r',', )),
        ('open', (r'\[', )),
        ('close', (r'\]', )),
        ('colon', (r':', )),
    ]
    ignore = ['space']
    tokenizer = make_tokenizer(specs)
    return [token for token in tokenizer(sig_str) if token.type not in ignore]
