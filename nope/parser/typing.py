import tokenize
import token

from funcparserlib.lexer import make_tokenizer
from funcparserlib.parser import (some, many, maybe, finished, forward_decl, skip)

from .. import nodes


class TypeComments(object):
    def __init__(self, explicit_types, type_definitions, generics):
        self.explicit_types = explicit_types
        self.type_definitions = type_definitions
        self.generics = generics


def parse_type_comments(source):
    explicit_types = {}
    type_definitions = {}
    generics = {}
    
    for attached_node_position, (position, prefix, type_comment) in _type_comments(source):
        if prefix == "#:type":
            store = type_definitions
        elif prefix == "#:generic":
            store = generics
        elif prefix == "#::":
            store = explicit_types
        else:
            raise Exception("Unhandled case")
        
        store[attached_node_position] = position, type_comment
    
    return TypeComments(explicit_types, type_definitions, generics)
    


def _type_comments(source):
    tokens = tokenize.generate_tokens(source.readline)
    last_type_comment = None
    
    for token_type, token_str, position, _, _ in tokens:
        semantic_comment = _extract_semantic_comment(token_type, token_str)
        if semantic_comment is not None:
            prefix, parser = semantic_comment
            last_type_comment = position, prefix, parser(token_str[len(prefix):].strip())
        elif last_type_comment is not None and _is_part_of_node(token_type):
            yield position, last_type_comment
            last_type_comment = None


def _extract_semantic_comment(token_type, token_str):
    if token_type == tokenize.COMMENT:
        for prefix, rule in _type_comment_parsers.items():
            if token_str.startswith(prefix):
                return prefix, lambda string: _parse(string, rule)


def _is_part_of_node(token_type):
    return token_type not in (
        token.NEWLINE, token.INDENT, token.DEDENT, tokenize.NL, tokenize.COMMENT
    )


def parse_explicit_type(sig_str):
    return _parse(sig_str, _explicit_type)


def _parse(string, rule):
    tokens = _tokenize_type_string(string)
    return rule.parse(tokens)


def _token_type(token_type):
    return some(lambda token: token.type == token_type)


def _make_name(result):
    return result.value


def _make_type_ref(result):
    return nodes.ref(result)


def _make_apply(result):
    return nodes.type_apply(result[0], result[1])


def _make_params(result):
    if result is None:
        return result
    else:
        return [nodes.formal_type_parameter(result[0])]


def _make_arg(result):
    return nodes.signature_arg(result[1], result[2], optional=result[0] is not None)
    

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


def _make_union_type(result):
    if len(result) == 1:
        return result[0]
    else:
        return nodes.type_union(result)


def _make_type_definition(result):
    return nodes.TypeDefinition(result[0], result[1])


def _make_generic(result):
    return list(map(nodes.formal_type_parameter, result))


def _create_type_rules():
    comma = _token_type("comma")
    colon = _token_type("colon")
    question_mark = _token_type("question-mark")
    bar = _token_type("bar")
    equals = _token_type("equals")
    
    type_name = arg_name = _token_type("name") >> _make_name

    primary_type = forward_decl()
    union_type = _one_or_more_with_separator(primary_type, bar) >> _make_union_type
    type_ = union_type
    
    type_ref = type_name >> _make_type_ref
    applied_type = (
        type_ref +
        skip(_token_type("open")) +
        _one_or_more_with_separator(type_, comma) +
        skip(_token_type("close"))
    ) >> _make_apply
    
    arg = (maybe(question_mark) + maybe(arg_name + skip(colon)) + type_) >> _make_arg
    
    generic_params = maybe(type_name + _token_type("fat-arrow")) >> _make_params
    args = maybe(arg + many(comma + arg)) >> _make_args
    signature = (generic_params + args + _token_type("arrow") + type_) >> _make_signature
    sub_signature = (_token_type("paren-open") + signature + _token_type("paren-close")) >> (lambda result: result[1])
    
    primary_type.define(sub_signature | applied_type | type_ref)
    explicit_type = (signature | type_) + finished >> (lambda result: result[0])
    
    type_definition = (type_name + skip(equals) + type_ + skip(finished))  >> _make_type_definition
    
    generic = (_one_or_more_with_separator(type_name, comma) + skip(finished)) >> _make_generic
    
    return explicit_type, type_definition, generic


def _one_or_more_with_separator(repeated, separator):
    return (repeated + many(skip(separator) + repeated)) >> _make_separated

def _make_separated(result):
    if result[1]:
        return [result[0]] + result[1]
    else:
        return [result[0]]


_explicit_type, _type_definition, _generic  = _create_type_rules()
    
    
def _tokenize_type_string(sig_str):
    specs = [
        ('space', (r'[ \t]+', )),
        ('name', (r'[A-Za-z_][A-Za-z_0-9]*', )),
        ('fat-arrow', (r'=>', )),
        ('arrow', (r'->', )),
        ('comma', (r',', )),
        ('open', (r'\[', )),
        ('close', (r'\]', )),
        ('paren-open', (r'\(', )),
        ('paren-close', (r'\)', )),
        ('colon', (r':', )),
        ('question-mark', (r'\?', )),
        ('bar', (r'\|', )),
        ('equals', (r'=', )),
    ]
    ignore = ['space']
    tokenizer = make_tokenizer(specs)
    return [token for token in tokenizer(sig_str) if token.type not in ignore]


_type_comment_parsers = {
    "#:type": _type_definition,
    "#:generic": _generic,
    "#::": _explicit_type,
}
