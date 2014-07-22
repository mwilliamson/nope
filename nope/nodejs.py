import os

from . import nodes, js


def nope_to_nodejs(source_path, nope_ast, destination_dir):
    source_filename = os.path.basename(source_path)
    dest_filename = source_filename[:source_filename.rindex(".")] + ".js"
    dest_path = os.path.join(destination_dir, dest_filename)
    with open(dest_path, "w") as dest_file:
        dest_file.write(_prelude)
        js.dump(_transform(nope_ast), dest_file)


_prelude = """
function print(value) {
    console.log(value);
}
"""


def _transform(nope_node):
    return _transformers[type(nope_node)](nope_node)


def _module(module):
    return js.statements(_transform_all(module.body))


def _expression_statement(statement):
    return js.expression_statement(_transform(statement.value))


def _call(call):
    return js.call(_transform(call.func), _transform_all(call.args))


def _ref(ref):
    return js.ref(ref.name)


def _int(node):
    return js.number(node.value)


def _transform_all(nodes):
    return list(map(_transform, nodes))


_transformers = {
    nodes.Module: _module,
    nodes.ExpressionStatement: _expression_statement,
    nodes.Call: _call,
    nodes.VariableReference: _ref,
    nodes.IntExpression: _int,
}
