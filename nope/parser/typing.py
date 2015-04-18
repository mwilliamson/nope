import tokenize
import token

from funcparserlib.lexer import make_tokenizer
from funcparserlib.parser import (some, many, maybe, finished, forward_decl, skip)

from .. import nodes


class Notes(object):
    def __init__(self, explicit_types, type_definitions, generics, fields):
        self.explicit_types = explicit_types
        self.type_definitions = type_definitions
        self.generics = generics
        self.fields = fields


def parse_notes(source):
    explicit_types = {}
    type_definitions = {}
    generics = {}
    # TODO: open up the parser for extension
    fields = {}
    
    for attached_node_position, (position, prefix, note) in _notes(source):
        if prefix in ["type", "structural-type"]:
            store = type_definitions
        elif prefix == "generic":
            store = generics
        elif prefix == "field":
            store = fields
        elif prefix == ":":
            store = explicit_types
        else:
            raise Exception("Unhandled case")
        
        store[attached_node_position] = position, note
    
    return Notes(explicit_types, type_definitions, generics, fields)
    


def _notes(source):
    tokens = tokenize.generate_tokens(source.readline)
    lines = []
    note_position = None
    
    for token_type, token_str, position, _, _ in tokens:
        line = _extract_note_line(token_type, token_str)
        if line is not None:
            lines.append(line)
            if note_position is None:
                note_position = position
        elif lines and _is_part_of_node(token_type):
            note = " ".join(lines).strip()
            for prefix, rule in _note_parsers.items():
                if note.startswith(prefix):
                    yield position, (note_position, prefix, _parse(note[len(prefix):], rule))
                    
            lines = []
            note_position = None


def _extract_note_line(token_type, token_str):
    if token_type == tokenize.COMMENT and token_str.startswith("#:"):
        return token_str[2:]


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
    return nodes.type_definition(result[0], result[1])


def _make_structural_type_definition(result):
    return nodes.structural_type(result[0], result[1])


def _make_generic(result):
    return list(map(nodes.formal_type_parameter, result))


def _create_type_rules():
    comma = _token_type("comma")
    colon = _token_type("colon")
    question_mark = _token_type("question-mark")
    bar = _token_type("bar")
    equals = _token_type("equals")
    
    attr_name = type_name = arg_name = _token_type("name") >> _make_name

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
    args = _zero_or_more_with_separator(arg, comma)
    signature = (generic_params + args + _token_type("arrow") + type_) >> _make_signature
    sub_signature = (_token_type("paren-open") + signature + _token_type("paren-close")) >> (lambda result: result[1])
    
    primary_type.define(sub_signature | applied_type | type_ref)
    explicit_type = (signature | type_) + finished >> (lambda result: result[0])
    
    type_definition = (type_name + skip(equals) + type_ + skip(finished))  >> _make_type_definition
    
    structural_type_attr = (attr_name + skip(colon) + explicit_type) >> tuple
    structural_type_attrs = many(structural_type_attr)
    
    structural_type_definition = (type_name + skip(colon) + structural_type_attrs + skip(finished)) >> _make_structural_type_definition
    
    generic = (_one_or_more_with_separator(type_name, comma) + skip(finished)) >> _make_generic
    
    return explicit_type, type_definition, structural_type_definition, generic


def _one_or_more_with_separator(repeated, separator):
    return (repeated + many(skip(separator) + repeated)) >> _make_separated

def _zero_or_more_with_separator(repeated, separator):
    return maybe(_one_or_more_with_separator(repeated, separator))

def _make_separated(result):
    if result[1]:
        return [result[0]] + result[1]
    else:
        return [result[0]]


_explicit_type, _type_definition, _structural_type_definition, _generic  = _create_type_rules()
    
    
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


_note_parsers = {
    "type": _type_definition,
    "structural-type": _structural_type_definition,
    "generic": _generic,
    ":": _explicit_type,
    "field": _explicit_type,
}
