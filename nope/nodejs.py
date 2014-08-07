import os

from . import nodes, js, util
from .walk import walk_tree


def nope_to_nodejs(source_path, source_tree, destination_dir):
    def handle_dir(path, relative_path):
        os.mkdir(os.path.join(destination_dir, relative_path))
    
    def handle_file(path, relative_path):
        _convert_file(path, source_tree.ast(path), os.path.dirname(os.path.join(destination_dir, relative_path)))
        
    walk_tree(source_path, handle_dir, handle_file)


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
    
    function isArray(value) {
        return Object.prototype.toString.call(value) === "[object Array]";
    }
    
    function isNumber(value) {
        return Object.prototype.toString.call(value) === "[object Number]";
    }
    
    var operators = {};
    ["add", "sub", "mul", "truediv", "floordiv"].forEach(function(operatorName) {
        operators[operatorName] = function(left, right) {
            if (isNumber(left)) {
                return numberOps[operatorName](left, right);
            } else {
                return left.__add__(right);
            }
        };
    });
    
    var numberOps = {
        add: function(left, right) {
            return left + right;
        },
        sub: function(left, right) {
            return left - right;
        },
        mul: function(left, right) {
            return left * right;
        },
        truediv: function(left, right) {
            return left / right;
        },
        floordiv: function(left, right) {
            return Math.floor(left / right);
        }
    };
    
    if (require.main === module) {
        // TODO: is there a way to resolve this at compile-time?
        //       This would require the user to specify which modules are going to be executed directly
        var $require = require;
        global.$nopeRequire = function(name) {
            if (isAbsoluteImport(name)) {
                var relativeImportName = "./" + name;
                if (isValidModulePath(relativeImportName)) {
                    return $require(relativeImportName);
                }
            }
            
            return $require(name);
        };
    }
    
    function isAbsoluteImport(name) {
        return name.indexOf(".") !== 0;
    }
    
    function isValidModulePath(name) {
        try {
            $require.resolve(name);
            return true;
        } catch(error) {
            return false;
        }
    }
    
    function bool(value) {
        // TODO: add support for __len__ and __iszero__
        if (isArray(value)) {
            return value.length > 0;
        }
        
        return !!value;
    }
    
    $nope = {
        propertyAccess: propertyAccess,
        require: global.$nopeRequire || require,
        exports: exports,
        operators: operators,
        
        bool: bool
    };
})();

bool = $nope.bool;
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
                        js.ref("$nope.exports"),
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
        
        return js.call(js.ref("$nope.require"), [js.string(module_path)])


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
            js.call(js.ref("$nope.bool"), [self.transform(statement.condition)]),
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
        operator_func = "$nope.operators.{}".format(operation.operator)
        return js.call(
            js.ref(operator_func),
            [self.transform(operation.left), self.transform(operation.right)]
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
