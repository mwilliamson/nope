import os
import shutil
import inspect

from . import js
from ... import nodes, types, name_declaration, returns, modules, module_resolution, builtins
from ...walk import walk_tree


def nope_to_nodejs(source_path, source_tree, checker, destination_dir, optimise=True):
    def handle_dir(path, relative_path):
        os.mkdir(os.path.join(destination_dir, relative_path))
    
    def handle_file(path, relative_path):
        module = source_tree.module(path)
        
        module_exports = modules.ModuleExports(name_declaration.DeclarationFinder())
        module_resolver = module_resolution.ModuleResolver(
            source_tree,
            builtins.builtin_modules,
            module_exports,
            module,
        )
        _convert_file(
            module_resolver,
            path,
            relative_path,
            module.node,
            checker.type_lookup(module),
            destination_dir,
            optimise=optimise,
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


def _convert_file(module_resolver, source_path, relative_path, nope_ast, type_lookup, destination_root, optimise):
    destination_dir = os.path.dirname(os.path.join(destination_root, relative_path))
    
    source_filename = os.path.basename(source_path)
    dest_filename = _js_filename(source_filename)
    dest_path = os.path.join(destination_dir, dest_filename)
    with open(dest_path, "w") as dest_file:
        _generate_prelude(dest_file, nope_ast, relative_path)
        js.dump(transform(nope_ast, type_lookup, module_resolver, optimise=optimise), dest_file)


def _js_filename(python_filename):
    if python_filename == "__init__.py":
        return "index.js"
    else:
        return _replace_extension(python_filename, "js")


def _replace_extension(filename, new_extension):
    return filename[:filename.rindex(".")] + "." + new_extension


# TODO: should probably yank this from somewhere more general since it's not specific to node.js
_builtin_names = [
    "bool", "print", "abs", "divmod", "range", "Exception", "AssertionError", "str",
]


def _call_internal(parts, args):
    return js.call(js.ref(".".join(["$nope"] + parts)), args)


_number_operators = {
    "add": lambda left, right: js.binary_operation("+", left, right),
    "sub": lambda left, right: js.binary_operation("-", left, right),
    "mul": lambda left, right: js.binary_operation("*", left, right),
    "truediv": lambda left, right: js.binary_operation("/", left, right),
    "floordiv": lambda left, right: _call_internal(["numberFloor"], [js.binary_operation("/", left, right)]),
    "mod": lambda left, right: _call_internal(["numberMod"], [left, right]),
    "divmod": lambda left, right: _call_internal(["numberDivMod"], [left, right]),
    "pow": lambda left, right: _call_internal(["numberPow"], [left, right]),
    # TODO: raise error on negative shifts
    "lshift": lambda left, right: js.binary_operation("<<", left, right),
    # TODO: raise error on negative shifts
    "rshift": lambda left, right: js.binary_operation(">>", left, right),
    "and": lambda left, right: js.binary_operation("&", left, right),
    "or": lambda left, right: js.binary_operation("|", left, right),
    "xor": lambda left, right: js.binary_operation("^", left, right),
    
    "neg": lambda operand: js.unary_operation("-", operand),
    "pos": lambda operand: js.unary_operation("+", operand),
    "abs": lambda operand: js.call(js.ref("Math.abs"), [operand]),
    "invert": lambda operand: js.unary_operation("~", operand),
    
    "eq": lambda left, right: js.binary_operation("==", left, right),
    "ne": lambda left, right: js.binary_operation("!=", left, right),
    "lt": lambda left, right: js.binary_operation("<", left, right),
    "le": lambda left, right: js.binary_operation("<=", left, right),
    "gt": lambda left, right: js.binary_operation(">", left, right),
    "ge": lambda left, right: js.binary_operation(">=", left, right),
    
    "str": lambda operand: js.call(js.property_access(operand, "toString"), []),
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


def transform(nope_node, type_lookup, module_resolver, optimise=True):
    module_exports = modules.ModuleExports(name_declaration.DeclarationFinder())
    transformer = Transformer(
        type_lookup,
        module_resolver,
        module_exports,
        optimise=optimise,
    )
    return transformer.transform(nope_node)


class Transformer(object):
    def __init__(self, type_lookup, module_resolver, module_exports, optimise):
        self._type_lookup = type_lookup
        self._module_resolver = module_resolver
        self._module_exports = module_exports
        self._declarations = name_declaration.DeclarationFinder()
        self._optimise = optimise
        
        self._transformers = {
            nodes.Module: self._module,
            nodes.Import: self._import,
            nodes.ImportFrom: self._import_from,
            
            nodes.ExpressionStatement:self. _expression_statement,
            nodes.Assignment: self._assign,
            nodes.ClassDefinition: self._class_definition,
            nodes.FunctionDef: self._function_def,
            nodes.ReturnStatement: self._return_statement,
            nodes.IfElse: self._if_else,
            nodes.WhileLoop: self._while_loop,
            nodes.ForLoop: self._for_loop,
            nodes.BreakStatement: self._break_statement,
            nodes.ContinueStatement: self._continue_statement,
            nodes.TryStatement: self._try_statement,
            nodes.RaiseStatement: self._raise_statement,
            nodes.AssertStatement: self._assert_statement,
            nodes.WithStatement: self._with_statement,
            
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
            nodes.ListLiteral: self._list_literal,
            nodes.TupleLiteral: self._tuple_literal,
            
            ConvertedNode: lambda node: node.js_node,
        }
        
        self._optimised_transformers = {
            nodes.BinaryOperation: self._optimised_binary_operation,
            nodes.UnaryOperation: self._optimised_unnary_operation,
        }
        
        self._unique_name_index = 0
    
    def transform(self, nope_node):
        node_type = type(nope_node)
        if self._optimise and node_type in self._optimised_transformers:
            result = self._optimised_transformers[node_type](nope_node)
            if result is not None:
                return result
        
        return self._transformers[node_type](nope_node)
    
    def _module(self, module):
        var_statements = [
            js.var(name)
            for name in sorted(self._declarations.declarations_in_module(module).names())
        ]
        body_statements = var_statements + self._transform_all(module.body)
        export_names = self._module_exports.names(module)
                
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
        statements = [
        ]
        
        for alias in import_from.names:
            import_value = self._import_module_expr(import_from.module, alias.name)
            statements.append(js.assign_statement(alias.value_name, import_value))
        
        return js.statements(statements)
    
    
    def _import_module_expr(self, module_name, value_name=None):
        module, attr_name = self._module_resolver.resolve_import_value(module_name, value_name)
        
        # TODO: push this logic into a separate class
        if attr_name is None and value_name is not None:
            path_parts = module_name + [value_name]
        else:
            path_parts = module_name
            
        module_path = "/".join(path_parts)
        if module_path.endswith("."):
            module_path += "/"
        
        module_expr = js.call(js.ref("$require"), [js.string(module_path)])
        
        if attr_name is None:
            return module_expr
        else:
            return js.property_access(module_expr, attr_name)    


    def _expression_statement(self, statement):
        return js.expression_statement(self.transform(statement.value))


    def _assign(self, assignment):
        value = self.transform(assignment.value)
        
        tmp_name = self._unique_name("tmp")
        assignments = [
            self._create_single_assignment(target, js.ref(tmp_name))
            for target in assignment.targets
        ]
        return js.statements([js.var(tmp_name, value)] + assignments)
    
    def _create_single_assignment(self, target, value):
        if isinstance(target, nodes.Subscript):
            call = self._operation(
                "setitem",
                [target.value, target.slice, ConvertedNode(value)]
            )
            return js.expression_statement(call)
        elif isinstance(target, nodes.TupleLiteral):
            return js.statements([
                self._create_single_assignment(target_element, js.property_access(value, js.number(index)))
                for index, target_element in enumerate(target.elements)
            ])
        # TODO: test this! Is using setattr necessary?
        elif isinstance(target, nodes.AttributeAccess):
            return js.assign_statement(
                js.property_access(self.transform(target.value), target.attr),
                value
            )
        elif isinstance(target, nodes.VariableReference):
            return js.assign_statement(self.transform(target), value)
        else:
            raise Exception("Unhandled case")
        
    
    def _class_definition(self, class_definition):
        # TODO: come up with a more general way of detecting names that only
        # occur at compile-time and removing them from actual output
        declared_names = list(self._declarations.declarations_in_class(class_definition).names())
        declared_names.remove("Self")
        declared_names.sort()
        
        renamed_methods, method_definitions = self._transform_class_methods(class_definition.body)
        
        if "__init__" in declared_names:
            init_type = self._type_of(class_definition).attrs.type_of("__call__")
            # The type checker should guarantee that init_type exists and
            # is a function type (a stronger constraint than simply callable)
            constructor_arg_names = [
                self._unique_name("arg")
                for arg in init_type.args
            ]
        else:
            constructor_arg_names = []
        
        self_name = self._unique_name("self")
        self_ref = js.ref(self_name)
        
        declare_self = js.var(self_name, js.obj({}))
        declarations = [js.var(name) for name in declared_names]
        execute_body = self._transform_class_body(class_definition.body, renamed_methods)
        assign_attrs = [
            js.assign_statement(
                js.property_access(self_ref, name),
                _call_internal(["instanceAttribute"], [self_ref, js.ref(name)])
            )
            for name in declared_names
            if name != "__init__"
        ]
        
        if "__init__" in declared_names:
            init_args = [self_ref] + [js.ref(name) for name in constructor_arg_names]
            call_init = [js.expression_statement(js.call(js.ref("__init__"), init_args))]
        else:
            call_init = []
        
        return_self = js.ret(js.ref(self_name))
        
        body = (
            [declare_self] +
            declarations +
            execute_body +
            assign_attrs +
            call_init + 
            [return_self]
        )
        
        assign_class = js.assign_statement(
            class_definition.name,
            js.function_expression(constructor_arg_names, body)
        )
        
        return js.statements(method_definitions + [assign_class])
    
    
    def _transform_class_methods(self, body):
        renamed_methods = {}
        method_definitions = []
        
        for statement in body:
            if isinstance(statement, nodes.FunctionDef):
                unique_name = self._unique_name(statement.name)
                renamed_methods[statement.name] = unique_name
                function = self.transform(statement)
                function.name = unique_name
                method_definitions.append(function)
        
        return renamed_methods, method_definitions
    
    
    def _transform_class_body(self, body, renamed_methods):
        return [
            self._transform_class_body_statement(statement, renamed_methods)
            for statement in body
        ]
    
    
    def _transform_class_body_statement(self, statement, renamed_methods):
        if isinstance(statement, nodes.FunctionDef):
            # Compound statements are not allowed in class bodies, so we don't
            # need to recurse
            name = statement.name
            return js.assign_statement(js.ref(name), js.ref(renamed_methods[name]));
        else:
            return self.transform(statement)
    
    
    def _function_def(self, func):
        declared_names = set(self._declarations.declarations_in_function(func).names())
        arg_names = [arg.name for arg in func.args.args]
        declared_names.difference_update(arg_names)
        
        body = [js.var(name) for name in declared_names] + self._transform_all(func.body)
        
        if not returns.has_unconditional_return(func.body):
            body += [js.ret(js.null)]
        
        return js.function_declaration(
            name=func.name,
            args=arg_names,
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
        return self._loop(loop, condition, at_loop_start=[])
        
    
    def _condition(self, condition):
        return self._builtins_bool(self.transform(condition))
    
    
    def _builtins_bool(self, js_condition):
        return _call_builtin("bool", [js_condition])
    
    
    def _for_loop(self, loop):
        iterator_name = self._unique_name("iterator")
        element_name = self._unique_name("element")
        sentinel = js.ref("$nope.loopSentinel")
        
        condition = js.binary_operation(
            "!==",
            js.assign(element_name, _call_builtin("next", [js.ref(iterator_name), sentinel])),
            sentinel,
        )
        assign_loop_target = self._create_single_assignment(loop.target, js.ref(element_name))
        
        return js.statements([
            js.var(iterator_name, _call_builtin("iter", [self.transform(loop.iterable)])),
            js.var(element_name),
            self._loop(loop, condition, at_loop_start=[assign_loop_target]),
        ])
    
    def _loop(self, loop, condition, at_loop_start):
        body = at_loop_start + self._transform_all(loop.body)
        
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
    
    
    def _break_statement(self, statement):
        return js.break_statement()
    
    
    def _continue_statement(self, statement):
        return js.continue_statement()


    def _try_statement(self, statement):
        exception_name = self._unique_name("exception")
        if statement.handlers:
            js_handler = js.throw(js.ref(exception_name))
            
            for handler in reversed(statement.handlers):
                if handler.type:
                    handler_type = self.transform(handler.type)
                else:
                    handler_type = js.ref("$nope.builtins.Exception")
                
                nope_exception = self._get_nope_exception_from_error(js.ref(exception_name))
                    
                handler_body = []
                if handler.target is not None:
                    handler_body.append(js.var(handler.target.name, nope_exception))
                
                handler_body += self._transform_all(handler.body)
                
                js_handler = js.if_else(
                    _call_builtin("isinstance", [nope_exception, handler_type]),
                    handler_body,
                    [js_handler],
                )
            
            js_handler = js.if_else(
                self._is_undefined(nope_exception),
                [js.throw(js.ref(exception_name))],
                [js_handler],
            )
        else:
            js_handler = None
        
        body = self._transform_all(statement.body)
        finally_body = self._transform_all(statement.finally_body)
        
        if js_handler or finally_body:
            return js.try_catch(
                body,
                exception_name,
                [js_handler] if js_handler else None,
                finally_body=finally_body,
            )
        else:
            return js.statements(body)
    
    def _raise_statement(self, statement):
        exception_value = self.transform(statement.value)
        return self._generate_raise(exception_value)
    
    
    def _assert_statement(self, statement):
        if statement.message is None:
            message = js.string("")
        else:
            message = self.transform(statement.message)
        
        exception_value = _call_builtin("AssertionError", [message])
        
        return js.if_else(
            self._condition(statement.condition),
            [],
            [self._generate_raise(exception_value)],
        )
    
    
    def _generate_raise(self, exception_value):
        exception_name = self._unique_name("exception")
        error_name = self._unique_name("error")
        
        exception_type = _call_builtin("type", [js.ref(exception_name)])
        exception_type_name = _call_builtin("getattr", [exception_type, js.string("__name__")])
        error_message = js.binary_operation("+",
            js.binary_operation("+",
                exception_type_name,
                js.string(": "),
            ),
            _call_builtin("str", [js.ref(exception_name)])
        )
        js_error = js.call(
            # TODO: create a proper `new` JS node
            js.ref("new $nope.Error"),
            # TODO: set message? Perhaps set as a getter
            []
        )
        
        return js.statements([
            js.var(exception_name, exception_value),
            js.var(error_name, js_error),
            js.expression_statement(js.assign(
                self._get_nope_exception_from_error(js.ref(error_name)),
                js.ref(exception_name)
            )),
            js.expression_statement(js.assign(
                js.property_access(js.ref(error_name), "toString"),
                js.function_expression([], [js.ret(error_message)])
            )),
            js.throw(js.ref(error_name)),
        ])
    
    
    def _with_statement(self, statement):
        exception_name = self._unique_name("exception")
        manager_name = self._unique_name("manager")
        exit_method_var_name = self._unique_name("exit")
        error_name = self._unique_name("error")
        has_exited_name = self._unique_name("hasExited")
        
        manager_ref = js.ref(manager_name)
        
        enter_value = js.call(self._get_magic_method(manager_ref, "enter"), [])
        if statement.target is None:
            enter_statement = js.expression_statement(enter_value)
        else:
            enter_statement = self._create_single_assignment(statement.target, enter_value)
        
        return js.statements([
            js.var(manager_name, self.transform(statement.value)),
            js.var(exit_method_var_name, self._get_magic_method(manager_ref, "exit")),
            js.var(has_exited_name, js.boolean(False)),
            enter_statement,
            js.try_catch(
                self._transform_all(statement.body),
                error_name=error_name,
                catch_body=[
                    js.var(exception_name, self._get_nope_exception_from_error(js.ref(error_name))),
                    js.assign_statement(js.ref(has_exited_name), js.boolean(True)),
                    js.if_else(
                        js.unary_operation("!", self._builtins_bool(js.call(js.ref(exit_method_var_name), [
                            _call_builtin("type", [js.ref(exception_name)]),
                            js.ref(exception_name),
                            js.null,
                        ]))),
                        [js.throw(js.ref(error_name))],
                        [],
                    ),
                    
                ],
                finally_body=[
                    js.if_else(
                        js.unary_operation("!", js.ref(has_exited_name)),
                        [
                            js.expression_statement(js.call(js.ref(exit_method_var_name), [js.null, js.null, js.null])),
                        ],
                        [],
                    ),
                ],
            ),
        ])


    def _call(self, call):
        # TODO: proper support for __call__
        # at the moment, we only support meta-types that are directly callable e.g. str()
        # a better solution might be have such values have a $call attribute (or similar)
        # to avoid clashing with actual __call__ attributes
        args = []
        
        call_func_type = self._type_of(call.func)
        while not types.is_func_type(call_func_type):
            call_func_type = call_func_type.attrs.type_of("__call__")
        
        for index, formal_arg in enumerate(call_func_type.args):
            if index < len(call.args):
                actual_arg_node = call.args[index]
            else:
                actual_arg_node = call.kwargs[formal_arg.name]
                
            args.append(self.transform(actual_arg_node))
            
        return js.call(self.transform(call.func), args)

    def _attr(self, attr):
        return self._getattr(self.transform(attr.value), attr.attr)
    
    def _binary_operation(self, operation):
        if operation.operator == "bool_and":
            return _call_internal(
                ["booleanAnd"],
                [self.transform(operation.left), self.transform(operation.right)]
            )
        elif operation.operator == "bool_or":
            return _call_internal(
                ["booleanOr"],
                [self.transform(operation.left), self.transform(operation.right)]
            )
        elif operation.operator == "is":
            return js.binary_operation("===",
                self.transform(operation.left),
                self.transform(operation.right))
        else:
            return self._operation(operation.operator, [operation.left, operation.right])
    
    def _optimised_binary_operation(self, operation):
        if (operation.operator in _number_operators and
                self._type_of(operation.left) == types.int_type and
                self._type_of(operation.right) == types.int_type):
            return _number_operators[operation.operator](
                self.transform(operation.left),
                self.transform(operation.right),
            )
    
    
    def _unary_operation(self, operation):
        if operation.operator == "bool_not":
            return js.unary_operation("!", self._condition(operation.operand))
        else:
            return self._operation(operation.operator, [operation.operand])
    
    def _optimised_unnary_operation(self, operation):
        if (operation.operator in _number_operators and
                self._type_of(operation.operand) == types.int_type):
            return _number_operators[operation.operator](self.transform(operation.operand))
    
    def _operation(self, operator_name, operands):
        return _call_internal(
            ["operators", operator_name],
            [self.transform(operand) for operand in operands],
        )
    
    def _get_magic_method(self, receiver, name):
        # TODO: get magic method through the same mechanism as self._call
        return self._getattr(receiver, "__{}__".format(name))
    
    def _subscript(self, subscript):
        return self._operation("getitem", [subscript.value, subscript.slice])


    def _list_literal(self, node):
        return js.array(self._transform_all(node.elements))
    
    
    def _tuple_literal(self, node):
        elements = js.array(self._transform_all(node.elements))
        return _call_internal(["jsArrayToTuple"], [elements])
    
    
    def _getattr(self, value, attr_name):
        return _call_builtin("getattr", [value, js.string(attr_name)])
    
    
    def _get_nope_exception_from_error(self, error):
        return js.property_access(error, "$nopeException")


    def _transform_all(self, nodes):
        return list(map(self.transform, nodes))
    
    
    def _type_of(self, node):
        return self._type_lookup.type_of(node)
    
    def _unique_name(self, base):
        name = "${}{}".format(base, self._unique_name_index)
        self._unique_name_index += 1
        return name
    
    def _is_undefined(self, value):
        return js.binary_operation("===", value, js.ref("$nope.undefined"))


def _call_builtin(name, args):
    return _call_internal(["builtins", name], args)


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


class ConvertedNode(object):
    def __init__(self, js_node):
        self.js_node = js_node
