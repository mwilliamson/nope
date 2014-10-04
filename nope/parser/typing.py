import tokenize
import token

from funcparserlib.lexer import make_tokenizer
from funcparserlib.parser import (some, many, maybe, finished, forward_decl, skip)

from .. import nodes


def parse_signatures(source):
    return dict(_signatures(source))


_comment_prefix = "#::"

def _signatures(source):
    tokens = tokenize.generate_tokens(source.readline)
    last_signature = None
    
    for token_type, token_str, position, _, _ in tokens:
        if _is_signature_comment(token_type, token_str):
            last_signature = parse_signature(token_str[len(_comment_prefix):].strip())
        elif last_signature is not None and _is_part_of_node(token_type):
            yield position, last_signature
            last_signature = None


def _is_signature_comment(token_type, token_str):
    return token_type == tokenize.COMMENT and token_str.startswith(_comment_prefix)


def _is_part_of_node(token_type):
    return token_type not in (
        token.NEWLINE, token.INDENT, token.DEDENT, tokenize.NL, tokenize.COMMENT
    )


def parse_signature(sig_str):
    tokens = _tokenize_signature(sig_str)
    return _signature.parse(tokens)


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

