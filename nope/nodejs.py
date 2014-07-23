import os

from . import nodes, js


def nope_to_nodejs(source_path, nope_ast, destination_dir):
    source_filename = os.path.basename(source_path)
    dest_filename = source_filename[:source_filename.rindex(".")] + ".js"
    dest_path = os.path.join(destination_dir, dest_filename)
    with open(dest_path, "w") as dest_file:
        dest_file.write(_prelude)
        js.dump(transform(nope_ast), dest_file)


_prelude = """
function print(value) {
    console.log(value);
}
"""


def transform(nope_node):
    return _transformers[type(nope_node)](nope_node)


def _module(module):
    return js.statements(_transform_all(module.body))


def _expression_statement(statement):
    return js.expression_statement(transform(statement.value))


def _function_def(func):
    return js.function_declaration(
        name=func.name,
        args=[arg.name for arg in func.args.args],
        body=_transform_all(func.body),
    )


def _return_statement(statement):
    return js.ret(transform(statement.value))


def _call(call):
    return js.call(transform(call.func), _transform_all(call.args))


def _ref(ref):
    return js.ref(ref.name)


def _int(node):
    return js.number(node.value)


def _transform_all(nodes):
    return list(map(transform, nodes))


_transformers = {
    nodes.Module: _module,
    
    nodes.ExpressionStatement: _expression_statement,
    nodes.FunctionDef: _function_def,
    nodes.ReturnStatement: _return_statement,
    
    nodes.Call: _call,
    nodes.VariableReference: _ref,
    nodes.IntExpression: _int,
}
