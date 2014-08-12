import os
import shutil
import inspect

from . import js
from ... import nodes, util, types
from ...walk import walk_tree


def nope_to_nodejs(source_path, source_tree, destination_dir):
    def handle_dir(path, relative_path):
        os.mkdir(os.path.join(destination_dir, relative_path))
    
    def handle_file(path, relative_path):
        _convert_file(
            path,
            relative_path,
            source_tree.ast(path),
            source_tree.type_lookup(path),
            destination_dir,
        )
    
    _write_nope_js(destination_dir)
    
    walk_tree(source_path, handle_dir, handle_file)


def _write_nope_js(destination_dir):
    nope_js_path = os.path.join(os.path.dirname(__file__), "nope.js")
    with open(os.path.join(destination_dir, "$nope.js"), "w") as dest_file:
        js.dump(_number_methods_ast(), dest_file)
        
        with open(os.path.join(nope_js_path)) as source_file:
            shutil.copyfileobj(source_file, dest_file)


def _number_methods_ast():
    return js.var("numberMethods", js.obj(dict(
        ("__{}__".format(name), _generate_number_method(generate_operation))
        for name, generate_operation in _number_operators.items()
    )))


def _generate_number_method(generate_operation):
    number_of_args = inspect.getargspec(generate_operation)[0]
    if len(number_of_args) == 1:
        return js.function_expression([], [
            js.ret(generate_operation(js.ref("this")))
        ])
    else:
        return js.function_expression(["right"], [
            js.ret(generate_operation(js.ref("this"), js.ref("right")))
        ])


def _convert_file(source_path, relative_path, nope_ast, type_lookup, destination_root):
    destination_dir = os.path.dirname(os.path.join(destination_root, relative_path))
    
    source_filename = os.path.basename(source_path)
    dest_filename = _js_filename(source_filename)
    dest_path = os.path.join(destination_dir, dest_filename)
    with open(dest_path, "w") as dest_file:
        _generate_prelude(dest_file, nope_ast, relative_path)
        js.dump(transform(nope_ast, type_lookup), dest_file)


def _js_filename(python_filename):
    if python_filename == "__init__.py":
        return "index.js"
    else:
        return _replace_extension(python_filename, "js")


def _replace_extension(filename, new_extension):
    return filename[:filename.rindex(".")] + "." + new_extension


# TODO: should probably yank this from somewhere more general since it's not specific to node.js
_builtin_names = [
    "bool", "print", "abs", "range",
]

_number_operators = {
    "add": lambda left, right: js.binary_operation("+", left, right),
    "sub": lambda left, right: js.binary_operation("-", left, right),
    "mul": lambda left, right: js.binary_operation("*", left, right),
    "truediv": lambda left, right: js.binary_operation("/", left, right),
    "floordiv": lambda left, right: js.call(js.ref("Math.floor"), [js.binary_operation("/", left, right)]),
    "mod": lambda left, right: js.call(js.ref("$nope.numberMod"), [left, right]),
    
    "neg": lambda operand: js.unary_operation("-", operand),
    "pos": lambda operand: js.unary_operation("+", operand),
    "abs": lambda operand: js.call(js.ref("Math.abs"), [operand]),
    "invert": lambda operand: js.unary_operation("~", operand),
}

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


def transform(nope_node, type_lookup):
    transformer = Transformer(type_lookup)
    return transformer.transform(nope_node)


class Transformer(object):
    def __init__(self, type_lookup):
        self._type_lookup = type_lookup
        
        self._transformers = {
            nodes.Module: self._module,
            nodes.Import: self._import,
            nodes.ImportFrom: self._import_from,
            
            nodes.ExpressionStatement:self. _expression_statement,
            nodes.Assignment: self._assign,
            nodes.FunctionDef: self._function_def,
            nodes.ReturnStatement: self._return_statement,
            nodes.IfElse: self._if_else,
            nodes.WhileLoop: self._while_loop,
            nodes.ForLoop: self._for_loop,
            nodes.BreakStatement: self._break_statement,
            nodes.ContinueStatement: self._continue_statement,
            
            nodes.Call: self._call,
            nodes.AttributeAccess: self._attr,
            nodes.BinaryOperation: self._binary_operation,
            nodes.UnaryOperation: self._unary_operation,
            nodes.Subscript: self._subscript,
            nodes.VariableReference: _ref,
            nodes.NoneExpression: _none,
            nodes.BooleanExpression: _bool,
            nodes.IntExpression: _int,
            nodes.StringExpression: _str,
            nodes.ListExpression: self._list,
        }
        
        self._unique_name_index = 0
    
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
        module_import_name = self._unique_name("import")
        
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
        
        if len(assignment.targets) == 1:
            return self._create_single_assignment(assignment.targets[0], value)
        
        tmp_name = self._unique_name("tmp")
        assignments = [
            self._create_single_assignment(target, js.ref(tmp_name))
            for target in assignment.targets
        ]
        return js.statements([js.var(tmp_name, value)] + assignments)
    
    def _create_single_assignment(self, target, value):
        if isinstance(target, nodes.Subscript):
            call = js.call(
                js.ref("$nope.operators.setitem"),
                [self.transform(target.value), self.transform(target.slice), value]
            )
            return js.expression_statement(call)
        else:
            return js.assign_statement(self.transform(target), value)
        

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
            self._condition(statement.condition),
            self._transform_all(statement.true_body),
            self._transform_all(statement.false_body),
        )
    
    
    def _while_loop(self, loop):
        condition = self._condition(loop.condition)
        body = self._transform_all(loop.body)
        
        if loop.else_body:
            else_body = self._transform_all(loop.else_body)
            
            normal_exit_name = self._unique_name("normalExit")
            normal_exit = js.ref(normal_exit_name)
            
            def assign_normal_exit(value):
                return js.assign_statement(normal_exit, js.boolean(value))
            
            return js.statements([
                js.var(normal_exit_name, js.boolean(True)),
                js.while_loop(
                    js.boolean(True),
                    # TODO: continue support
                    [assign_normal_exit(True)] +
                        [js.if_else(condition, [], [js.break_statement()])] +
                        [assign_normal_exit(False)] +
                        body,
                ),
                js.if_else(
                    normal_exit,
                    else_body,
                    []
                )
            ])
        else:
            return js.while_loop(
                condition,
                body,
            )
    
    def _condition(self, condition):
        return js.call(
            js.ref("$nope.builtins.bool"),
            [self.transform(condition)]
        )
    
    
    def _for_loop(self, loop):
        iterator_name = self._unique_name("iterator")
        element_name = self._unique_name("element")
        sentinel = js.ref("$nope.loopSentinel")
        return js.statements([
            js.var(iterator_name, js.call(js.ref("$nope.builtins.iter"), [self.transform(loop.iterable)])),
            js.var(element_name),
            js.while_loop(
                js.binary_operation(
                    "!==",
                    js.assign(element_name, js.call(js.ref("$nope.builtins.next"), [js.ref(iterator_name), sentinel])),
                    sentinel,
                ),
                [js.assign_statement(self.transform(loop.target), js.ref(element_name)),] + self._transform_all(loop.body),
            ),
        ])
    
    
    def _break_statement(self, statement):
        return js.break_statement()
    
    
    def _continue_statement(self, statement):
        return js.continue_statement()


    def _call(self, call):
        return js.call(self.transform(call.func), self._transform_all(call.args))


    def _attr(self, attr):
        return js.call(
            js.ref("$nope.builtins.getattr"),
            [self.transform(attr.value), js.string(attr.attr)],
        )
    
    def _binary_operation(self, operation):
        # TODO: document subclassing int (and other builtins) is prohibited (or rather, might misbehave) due to this optimisation
        if (operation.operator in _number_operators and
                self._type_of(operation.left) == types.int_type and
                self._type_of(operation.right) == types.int_type):
            return _number_operators[operation.operator](
                self.transform(operation.left),
                self.transform(operation.right),
            )
        else:
            return self._operation(operation, [operation.left, operation.right])
    
    
    def _unary_operation(self, operation):
        if (operation.operator in _number_operators and
                self._type_of(operation.operand) == types.int_type):
            return _number_operators[operation.operator](self.transform(operation.operand))
        else:
            return self._operation(operation, [operation.operand])
    
    def _operation(self, operation, operands):
        operator_func = "$nope.operators.{}".format(operation.operator)
        return js.call(
            js.ref(operator_func),
            [self.transform(operand) for operand in operands]
        )
    
    def _subscript(self, subscript):
        js_value = self.transform(subscript.value)
        js_slice = self.transform(subscript.slice)
        
        return js.call(
            js.ref("$nope.operators.getitem"),
            [js_value, js_slice]
        )


    def _list(self, node):
        return js.array(self._transform_all(node.elements))


    def _transform_all(self, nodes):
        return list(map(self.transform, nodes))
    
    
    def _type_of(self, node):
        return self._type_lookup.type_of(node)
    
    def _unique_name(self, base):
        name = "${}{}".format(base, self._unique_name_index)
        self._unique_name_index += 1
        return name


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

