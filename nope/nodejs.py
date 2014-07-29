import os

from . import nodes, js, util


def nope_to_nodejs(source_path, nope_ast, destination_dir):
    if os.path.isdir(source_path):
        _convert_dir(source_path, nope_ast, destination_dir)
    else:
        _convert_file(source_path, nope_ast, destination_dir)


def _convert_dir(source_path, source_tree, destination_dir):
    def _source_path_to_dest_path(source_full_path):
        relative_path = os.path.relpath(source_full_path, source_path)
        return os.path.join(destination_dir, relative_path)
    
    for root, dirnames, filenames in os.walk(source_path):
        for dirname in dirnames: 
            full_path = os.path.join(root, dirname)
            os.mkdir(_source_path_to_dest_path(full_path))
        
        for filename in filenames:
            full_path = os.path.join(root, filename)
            _convert_file(full_path, source_tree.ast(full_path), os.path.dirname(_source_path_to_dest_path(full_path)))
    


def _convert_file(source_path, nope_ast, destination_dir):
    source_filename = os.path.basename(source_path)
    if source_filename == "__init__.py":
        dest_filename = "index.js"
    else:
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
        propertyAccess: propertyAccess,
        require: require,
        exports: exports
    };
})();
"""


def transform(nope_node):
    return _transformers[type(nope_node)](nope_node)


def _module(module):
    body_statements = _generate_vars(module.body) + _transform_all(module.body)
    export_names = util.exported_names(module)
            
    export_statements = [
        js.expression_statement(
            js.assign(
                js.property_access(
                    js.ref("$nope.exports"),
                    export_name
                ),
                js.ref(export_name)
            )
        )
        for export_name in export_names
    ]
    return js.statements(body_statements + export_statements)


def _import_from(import_from):
    # TODO: generate import names to avoid clashes
    module_import_name = "$import0"
    module_path = "/".join(import_from.module)
    if module_path == ".":
        module_path = "./"
    if not module_path.startswith("."):
        module_path = "./" + module_path
    
    import_name_alias, = import_from.names
    import_name = import_name_alias.name
    assert import_name_alias.asname is None
    
    return js.statements([
        js.var(module_import_name),
        js.var(import_name),
        js.expression_statement(
            js.assign(module_import_name, js.call(js.ref("$nope.require"), [js.string(module_path)]))
        ),
        js.expression_statement(
            js.assign(import_name, js.property_access(js.ref(module_import_name), import_name))
        ),
    ])


def _expression_statement(statement):
    return js.expression_statement(transform(statement.value))


def _assign(assignment):
    value = transform(assignment.value)
    for name in reversed(assignment.targets):
        value = js.assign(name, value)
    return js.expression_statement(value)
    

def _function_def(func):
    body = _generate_vars(func.body) + _transform_all(func.body)
    
    return js.function_declaration(
        name=func.name,
        args=[arg.name for arg in func.args.args],
        body=body,
    )


def _generate_vars(statements):
    return [
        js.var(name)
        for name in util.declared_locals(statements)
    ]
    


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


def _list(node):
    return js.array(_transform_all(node.elements))


def _transform_all(nodes):
    return list(map(transform, nodes))


_transformers = {
    nodes.Module: _module,
    nodes.ImportFrom: _import_from,
    
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
    nodes.ListExpression: _list,
}
