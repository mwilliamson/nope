import os
import shutil

from . import js
from ... import nodes, util
from ...walk import walk_tree


def nope_to_nodejs(source_path, source_tree, destination_dir):
    def handle_dir(path, relative_path):
        os.mkdir(os.path.join(destination_dir, relative_path))
    
    def handle_file(path, relative_path):
        _convert_file(
            path,
            relative_path,
            source_tree.ast(path),
            destination_dir,
        )
    
    nope_js_path = os.path.join(os.path.dirname(__file__), "nope.js")
    shutil.copy(nope_js_path, os.path.join(destination_dir, "$nope.js"))
    
    walk_tree(source_path, handle_dir, handle_file)


def _convert_file(source_path, relative_path, nope_ast, destination_root):
    destination_dir = os.path.dirname(os.path.join(destination_root, relative_path))
    
    source_filename = os.path.basename(source_path)
    dest_filename = _js_filename(source_filename)
    dest_path = os.path.join(destination_dir, dest_filename)
    with open(dest_path, "w") as dest_file:
        _generate_prelude(dest_file, nope_ast, relative_path)
        js.dump(transform(nope_ast), dest_file)


def _js_filename(python_filename):
    if python_filename == "__init__.py":
        return "index.js"
    else:
        return _replace_extension(python_filename, "js")


def _replace_extension(filename, new_extension):
    return filename[:filename.rindex(".")] + "." + new_extension


# TODO: should probably yank this from somewhere more general since it's not specific to node.js
_builtin_names = [
    "bool", "print",
]

def _generate_prelude(fileobj, module, relative_path):
    relative_path = "../" * _path_depth(relative_path)
    
    fileobj.write("""var $nope = require("{}./$nope");\n""".format(relative_path));
    fileobj.write("""var $exports = exports;\n""".format(relative_path));
    if module.is_executable:
        fileobj.write(_main_require)
    fileobj.write("""var $require = global.$nopeRequire || require;\n""")
    
    for builtin_name in _builtin_names:
        builtin_assign = js.expression_statement(js.assign(
            builtin_name,
            js.property_access(js.ref("$nope.builtins"), builtin_name),
        ))
        js.dump(builtin_assign, fileobj)


def _path_depth(path):
    depth = -1
    while path:
        path, tail = os.path.split(path)
        depth += 1
    
    return depth
        

_main_require = """
(function() {
    if (require.main === module) {
        var originalRequire = require;
        global.$nopeRequire = function(name) {
            if (isAbsoluteImport(name)) {
                var relativeImportName = "./" + name;
                if (isValidModulePath(relativeImportName)) {
                    return $require(relativeImportName);
                }
            }
            
            return originalRequire(name);
        };
    }

    function isAbsoluteImport(name) {
        return name.indexOf(".") !== 0;
    }

    function isValidModulePath(name) {
        try {
            originalRequire.resolve(name);
            return true;
        } catch(error) {
            return false;
        }
    }
})();
"""


def transform(nope_node):
    transformer = Transformer()
    return transformer.transform(nope_node)


class Transformer(object):
    def __init__(self):
        self._transformers = {
            nodes.Module: self._module,
            nodes.Import: self._import,
            nodes.ImportFrom: self._import_from,
            
            nodes.ExpressionStatement:self. _expression_statement,
            nodes.Assignment: self._assign,
            nodes.FunctionDef: self._function_def,
            nodes.ReturnStatement: self._return_statement,
            nodes.IfElse: self._if_else,
            
            nodes.Call: self._call,
            nodes.AttributeAccess: self._attr,
            nodes.BinaryOperation: self._binary_operation,
            nodes.UnaryOperation: self._unary_operation,
            nodes.VariableReference: _ref,
            nodes.NoneExpression: _none,
            nodes.BooleanExpression: _bool,
            nodes.IntExpression: _int,
            nodes.StringExpression: _str,
            nodes.ListExpression: self._list,
        }
        
        self._import_index = 0
    
    def transform(self, nope_node):
        return self._transformers[type(nope_node)](nope_node)
    
    def _module(self, module):
        body_statements = _generate_vars(module.body) + self._transform_all(module.body)
        export_names = util.exported_names(module)
                
        export_statements = [
            js.expression_statement(
                js.assign(
                    js.property_access(
                        js.ref("$exports"),
                        export_name
                    ),
                    js.ref(export_name)
                )
            )
            for export_name in export_names
        ]
        return js.statements(body_statements + export_statements)


    def _import(self, import_node):
        statements = []
        
        for alias in import_node.names:
            if alias.asname is None:
                parts = alias.name_parts
                
                for index, part in enumerate(parts):
                    this_module_require = self._import_module_expr(parts[:index + 1])
                    
                    if index == 0:
                        this_module_ref = js.ref(part)
                        statements.append(js.assign_statement(part, this_module_require))
                    else:
                        this_module_ref = js.property_access(last_module_ref, part)
                        statements.append(js.assign_statement(
                            this_module_ref,
                            this_module_require
                        ))
                        
                    last_module_ref = this_module_ref
            else:
                statements.append(js.assign_statement(alias.value_name, self._import_module_expr(alias.name_parts)))
        
        return js.statements(statements)


    def _import_from(self, import_from):
        module_import_name = "$import{}".format(self._import_index)
        self._import_index += 1
        
        statements = [
            js.var(
                module_import_name,
                self._import_module_expr(import_from.module)
            )
        ]
        
        for alias in import_from.names:
            import_value = js.property_access(js.ref(module_import_name), alias.name)
            statements.append(js.assign_statement(alias.value_name, import_value))
        
        return js.statements(statements)
    
    
    def _import_module_expr(self, module_name):
        module_path = "/".join(module_name)
        if module_path.endswith("."):
            module_path += "/"
        
        return js.call(js.ref("$require"), [js.string(module_path)])


    def _expression_statement(self, statement):
        return js.expression_statement(self.transform(statement.value))


    def _assign(self, assignment):
        value = self.transform(assignment.value)
        for name in reversed(assignment.targets):
            value = js.assign(name, value)
        return js.expression_statement(value)
        

    def _function_def(self, func):
        body = _generate_vars(func.body) + self._transform_all(func.body)
        
        return js.function_declaration(
            name=func.name,
            args=[arg.name for arg in func.args.args],
            body=body,
        )
        


    def _return_statement(self, statement):
        return js.ret(self.transform(statement.value))


    def _if_else(self, statement):
        return js.if_else(
            js.call(js.ref("$nope.builtins.bool"), [self.transform(statement.condition)]),
            self._transform_all(statement.true_body),
            self._transform_all(statement.false_body),
        )


    def _call(self, call):
        return js.call(self.transform(call.func), self._transform_all(call.args))


    def _attr(self, attr):
        return js.call(
            js.ref("$nope.propertyAccess"),
            [self.transform(attr.value), js.string(attr.attr)],
        )
    
    def _binary_operation(self, operation):
        return self._operation(operation, [operation.left, operation.right])
    
    
    def _unary_operation(self, operation):
        return self._operation(operation, [operation.operand])
    
    def _operation(self, operation, operands):
        operator_func = "$nope.operators.{}".format(operation.operator)
        return js.call(
            js.ref(operator_func),
            [self.transform(operand) for operand in operands]
        )
        


    def _list(self, node):
        return js.array(self._transform_all(node.elements))


    def _transform_all(self, nodes):
        return list(map(self.transform, nodes))


def _generate_vars(statements):
    return [
        js.var(name)
        for name in util.declared_locals(statements)
    ]


def _ref(ref):
    return js.ref(ref.name)


def _none(none):
    return js.null


def _bool(boolean):
    return js.boolean(boolean.value)


def _int(node):
    return js.number(node.value)


def _str(node):
    return js.string(node.value)

