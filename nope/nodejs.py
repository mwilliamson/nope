import os

from . import nodes, js, util


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
(function() {
    function propertyAccess(value, propertyName) {
        if (isString(value) && propertyName === "find") {
            // TODO: perform this rewriting at compile-time
            return value.indexOf.bind(value);
        } else {
            // TODO: bind this if the property is a function
            return value[propertyName];
        }
    }
    
    function isString(value) {
        return Object.prototype.toString.call(value) === "[object String]";
    }

    $nope = {
        propertyAccess: propertyAccess
    };
})();
"""


def transform(nope_node):
    return _transformers[type(nope_node)](nope_node)


def _module(module):
    return js.statements(_transform_all(module.body))


def _expression_statement(statement):
    return js.expression_statement(transform(statement.value))


def _assign(assignment):
    value = transform(assignment.value)
    for name in reversed(assignment.targets):
        value = js.assign(name, value)
    return js.expression_statement(value)
    

def _function_def(func):
    var_declarations = [
        js.var(name)
        for name in util.declared_locals(func)
    ]
    
    body = var_declarations + _transform_all(func.body)
    
    return js.function_declaration(
        name=func.name,
        args=[arg.name for arg in func.args.args],
        body=body,
    )


def _return_statement(statement):
    return js.ret(transform(statement.value))


def _call(call):
    return js.call(transform(call.func), _transform_all(call.args))


def _attr(attr):
    return js.call(
        js.ref("$nope.propertyAccess"),
        [transform(attr.value), js.string(attr.attr)],
    )


def _ref(ref):
    return js.ref(ref.name)


def _none(none):
    return js.null


def _int(node):
    return js.number(node.value)


def _str(node):
    return js.string(node.value)


def _transform_all(nodes):
    return list(map(transform, nodes))


_transformers = {
    nodes.Module: _module,
    
    nodes.ExpressionStatement: _expression_statement,
    nodes.Assignment: _assign,
    nodes.FunctionDef: _function_def,
    nodes.ReturnStatement: _return_statement,
    
    nodes.Call: _call,
    nodes.AttributeAccess: _attr,
    nodes.VariableReference: _ref,
    nodes.NoneExpression: _none,
    nodes.IntExpression: _int,
    nodes.StringExpression: _str,
}
