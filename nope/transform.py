import ast

from . import nodes


def python_to_nope(python_ast):
    return _converters[type(python_ast)](python_ast)


def module(node):
    return nodes.module(_mapped(node.body))


def func(node):
    if node.returns is None:
        return_annotation = None
    else:
        return_annotation = python_to_nope(node.returns)
    
    return nodes.func(
        name=node.name,
        args=python_to_nope(node.args),
        return_annotation=return_annotation,
        body=_mapped(node.body),
    )


def expr(node):
    return nodes.expression_statement(python_to_nope(node.value))


def arguments(node):
    return nodes.arguments(_mapped(node.args))


def arg(node):
    return nodes.argument(node.arg, python_to_nope(node.annotation))


def str_literal(node):
    return nodes.str(node.s)


def num_literal(node):
    value = node.n
    if isinstance(value, int):
        return nodes.int(value)


def name(node):
    return nodes.ref(node.id)


def call(node):
    return nodes.call(python_to_nope(node.func), _mapped(node.args))


def _mapped(nodes):
    return [
        python_to_nope(node)
        for node in nodes
        if not isinstance(node, ast.Pass)
    ]

_converters = {
    ast.Module: module,
    ast.FunctionDef: func,
    ast.Expr: expr,
    
    ast.arguments: arguments,
    ast.arg: arg,
    
    ast.Str: str_literal,
    ast.Num: num_literal,
    ast.Name: name,
    ast.Call: call,
}

