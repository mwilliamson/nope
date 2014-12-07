import tokenize
import token
import ast

from funcparserlib.lexer import make_tokenizer
from funcparserlib.parser import (some, many, maybe, finished, forward_decl, skip)

from .. import nodes


def parse_type_statements(source):
    type_statements = sorted(_type_statements(source), key=lambda item: item[0], reverse=True)
    
    result = {}
    
    def consume_type_statements_before_node(node):
        while type_statements and type_statements[-1][0] < (node.lineno, node.col_offset):
            yield type_statements.pop()[1]
    
    class _TypeStatementVisitor(ast.NodeVisitor):
        def generic_visit(self, node):
            if hasattr(node, "lineno"):
                statements = list(consume_type_statements_before_node(node))
                if statements:
                    result[(node.lineno, node.col_offset)] = statements
            ast.NodeVisitor.generic_visit(self, node)
            
            
    _TypeStatementVisitor().visit(ast.parse(source.getvalue()))
    
    return result
    


_type_statement_prefix = "#:type"

def _type_statements(source):
    tokens = tokenize.generate_tokens(source.readline)
    
    for token_type, token_str, position, _, _ in tokens:
        if _is_semantic_comment(_type_statement_prefix, token_type, token_str):
            yield position, _parse_type_definition(token_str[len(_type_statement_prefix):].strip())
    

def parse_explicit_types(source):
    return dict(_explicit_types(source))


_comment_prefix = "#::"

def _explicit_types(source):
    tokens = tokenize.generate_tokens(source.readline)
    last_explicit_type = None
    
    for token_type, token_str, position, _, _ in tokens:
        if _is_signature_comment(token_type, token_str):
            last_explicit_type = position, parse_explicit_type(token_str[len(_comment_prefix):].strip())
        elif last_explicit_type is not None and _is_part_of_node(token_type):
            yield position, last_explicit_type
            last_explicit_type = None


def _is_signature_comment(token_type, token_str):
    return _is_semantic_comment(_comment_prefix, token_type, token_str)


def _is_semantic_comment(prefix, token_type, token_str):
    return token_type == tokenize.COMMENT and token_str.startswith(prefix)


def _is_part_of_node(token_type):
    return token_type not in (
        token.NEWLINE, token.INDENT, token.DEDENT, tokenize.NL, tokenize.COMMENT
    )


def _parse_type_definition(type_definition_str):
    tokens = _tokenize_type_string(type_definition_str)
    return _type_definition.parse(tokens)


def parse_explicit_type(sig_str):
    tokens = _tokenize_type_string(sig_str)
    return _explicit_type.parse(tokens)


def _token_type(token_type):
    return some(lambda token: token.type == token_type)


def _make_name(result):
    return result.value


def _make_type_ref(result):
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
    if result[1]:
        return nodes.type_union([result[0]] + [extra_type[1] for extra_type in result[1]])
    else:
        return result[0]


def _make_type_definition(result):
    return nodes.TypeDefinition(result[0], result[1])


def _create_type_rules():
    comma = _token_type("comma")
    colon = _token_type("colon")
    question_mark = _token_type("question-mark")
    bar = _token_type("bar")
    equals = _token_type("equals")
    
    type_name = arg_name = _token_type("name") >> _make_name

    primary_type = forward_decl()
    union_type = (primary_type + many(bar + primary_type)) >> _make_union_type
    type_ = union_type
    
    type_ref = type_name >> _make_type_ref
    applied_type = (type_ref + _token_type("open") + type_ + many(comma + type_) + _token_type("close")) >> _make_apply
    
    arg = (maybe(question_mark) + maybe(arg_name + skip(colon)) + type_) >> _make_arg
    
    generic_params = maybe(type_name + _token_type("fat-arrow")) >> _make_params
    args = maybe(arg + many(comma + arg)) >> _make_args
    signature = (generic_params + args + _token_type("arrow") + type_) >> _make_signature
    sub_signature = (_token_type("paren-open") + signature + _token_type("paren-close")) >> (lambda result: result[1])
    
    primary_type.define(sub_signature | applied_type | type_ref)
    explicit_type = (signature | type_) + finished >> (lambda result: result[0])
    
    type_definition = (type_ref + skip(equals) + type_ + skip(finished))  >> _make_type_definition
    
    return explicit_type, type_definition


_explicit_type, _type_definition  = _create_type_rules()
    
    
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

