import zuice

from ... import nodes, types, couscous as cc
from ...modules import ModuleExports, BuiltinModule
from ...name_declaration import DeclarationFinder
from ...module_resolution import ModuleResolver
from . import js, operations
from .internals import call_internal


optimise = zuice.key("optimise")


class NodeTransformer(zuice.Base):
    _module_resolver = zuice.dependency(ModuleResolver)
    _optimise = zuice.dependency(optimise)
    
    @zuice.init
    def init(self):
        self._transformers = {
            cc.Module: self._module,
            cc.Import: self._import,
            cc.ImportFrom: self._import_from,
            
            cc.ExpressionStatement:self. _expression_statement,
            cc.VariableDeclaration: self._declare,
            cc.Assignment: self._assign,
            cc.ClassDefinition: self._class_definition,
            cc.FunctionDefinition: self._function_def,
            cc.ReturnStatement: self._return_statement,
            cc.IfStatement: self._if_else,
            cc.WhileLoop: self._while_loop,
            cc.BreakStatement: self._break_statement,
            cc.ContinueStatement: self._continue_statement,
            cc.TryStatement: self._try_statement,
            cc.RaiseStatement: self._raise_statement,
            cc.Statements: self._statements,
            
            cc.Call: self._call,
            cc.AttributeAccess: self._attr,
            cc.BinaryOperation: self._binary_operation,
            cc.UnaryOperation: self._unary_operation,
            cc.VariableReference: _ref,
            cc.BuiltinReference: _builtin_ref,
            cc.InternalReference: _internal_ref,
            cc.NoneLiteral: _none,
            cc.BooleanLiteral: _bool,
            cc.IntLiteral: _int,
            cc.StrLiteral: _str,
            cc.ListLiteral: self._list_literal,
            cc.TupleLiteral: self._tuple_literal,
        }
        
        self._optimised_transformers = {
            nodes.BinaryOperation: self._optimised_binary_operation,
            nodes.UnaryOperation: self._optimised_unnary_operation,
        }
        
        self._unique_name_index = 0
        # TODO: find a nicer way of dealing with the handler stack
        # TODO: do we need to prevent re-raise if not in the scope of a handler?
        # or can we assume that that IR code is never generated?
        self._handler_stack = []
    
    def transform(self, nope_node):
        node_type = type(nope_node)
        if self._optimise and node_type in self._optimised_transformers:
            result = self._optimised_transformers[node_type](nope_node)
            if result is not None:
                return result
        
        if node_type in self._transformers:
            return self._transformers[node_type](nope_node)
        
        raise Exception("Could not transform node: {}".format(nope_node))
    
    def _module(self, module):
        body_statements = self._transform_all(module.body)
        
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
            for export_name in module.exported_names
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
        resolved_import = self._module_resolver.resolve_import_value(module_name, value_name)
        
        module_path = "/".join(resolved_import.module_name)
        if module_path.endswith("."):
            module_path += "/"
        
        if isinstance(resolved_import.module, BuiltinModule):
            module_path = "__builtins/{}".format(module_path)
        
        module_expr = js.call(js.ref("$require"), [js.string(module_path)])
        
        if resolved_import.attr_name is None:
            return module_expr
        else:
            return js.property_access(module_expr, resolved_import.attr_name)    


    def _expression_statement(self, statement):
        return js.expression_statement(self.transform(statement.value))


    def _declare(self, declaration):
        if declaration.value is None:
            return js.var(declaration.name)
        else:
            return js.var(declaration.name, self.transform(declaration.value))


    def _assign(self, assignment):
        value = self.transform(assignment.value)
        target = self.transform(assignment.target)
        return js.assign_statement(target, value)
        
    
    def _class_definition(self, class_definition):
        renamed_methods, method_definitions = self._transform_class_methods(class_definition.methods)
        declared_names = set(
            node.name
            for node in class_definition.body
            if isinstance(node, cc.VariableDeclaration)
        )
        if "__init__" in renamed_methods:
            init_method = next(method for method in class_definition.methods if method.name == "__init__")
            # The type checker should guarantee that init_type exists and
            # is a function type (a stronger constraint than simply callable)
            constructor_arg_names = [
                self._unique_name("arg")
                for arg_index in range(len(init_method.args) - 1)
            ]
        else:
            constructor_arg_names = []
        
        self_name = self._unique_name("self")
        self_ref = js.ref(self_name)
        
        declare_self = js.var(self_name, js.obj({}))
        execute_body = self._transform_class_body(class_definition.body)
        
        def create_attr_assignment(name, value):
            return js.assign_statement(
                js.property_access(self_ref, name),
                call_internal(["instanceAttribute"], [self_ref, value])
            )
        
        assign_attrs = [
            create_attr_assignment(name, js.ref(name))
            for name in declared_names
        ]
        
        assign_methods = [
            create_attr_assignment(method.name, js.ref(renamed_methods[method.name]))
            for method in class_definition.methods
            if method.name != "__init__"
        ]
        
        if "__init__" in renamed_methods:
            init_args = [self_ref] + [js.ref(name) for name in constructor_arg_names]
            call_init = [js.expression_statement(js.call(js.ref(renamed_methods["__init__"]), init_args))]
        else:
            call_init = []
        
        return_self = js.ret(js.ref(self_name))
        
        body = (
            [declare_self] +
            execute_body +
            assign_attrs +
            assign_methods +
            call_init + 
            [return_self]
        )
        
        assign_class = js.assign_statement(
            class_definition.name,
            js.function_expression(constructor_arg_names, body)
        )
        
        return js.statements(method_definitions + [assign_class])
    
    
    def _transform_class_methods(self, methods):
        renamed_methods = {}
        method_definitions = []
        
        for method in methods:
            unique_name = self._unique_name(method.name)
            renamed_methods[method.name] = unique_name
            function = self.transform(method)
            function.name = unique_name
            method_definitions.append(function)
        
        return renamed_methods, method_definitions
    
    
    def _transform_class_body(self, body):
        return list(map(self.transform, body))
    
    
    def _function_def(self, func):
        body = self._transform_all(func.body)
        
        return js.function_declaration(
            name=func.name,
            args=[arg.name for arg in func.args],
            body=body,
        )
        

    def _return_statement(self, statement):
        return js.ret(self.transform(statement.value))


    def _if_else(self, statement):
        return js.if_else(
            self.transform(statement.condition),
            self._transform_all(statement.true_body),
            self._transform_all(statement.false_body),
        )
    
    
    def _while_loop(self, loop):
        return js.while_loop(
            self.transform(loop.condition),
            self._transform_all(loop.body),
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
                
                self._handler_stack.append(exception_name)
                try:
                    handler_body += self._transform_all(handler.body)
                finally:
                    self._handler_stack.pop()
                
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
        if statement.value is None:
            return js.throw(js.ref(self._handler_stack[-1]))
        else:
            exception_value = self.transform(statement.value)
            return self._generate_raise(exception_value)
    
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
    
    
    def _statements(self, statements):
        return js.statements([self.transform(statement) for statement in statements.body])
    
    
    def _call(self, call):
        args = [self.transform(arg) for arg in call.args]
        return js.call(self.transform(call.func), args)

    def _attr(self, attr):
        return self._getattr(self.transform(attr.obj), attr.attr)
    
    def _binary_operation(self, operation):
        if operation.operator == "and":
            return call_internal(
                ["booleanAnd"],
                [self.transform(operation.left), self.transform(operation.right)]
            )
        elif operation.operator == "or":
            return call_internal(
                ["booleanOr"],
                [self.transform(operation.left), self.transform(operation.right)]
            )
        elif operation.operator == "is":
            return js.binary_operation("===",
                self.transform(operation.left),
                self.transform(operation.right))
        elif operation.operator == "is_not":
            return js.binary_operation("!==",
                self.transform(operation.left),
                self.transform(operation.right))
        else:
            raise Exception("Unrecognised binary operator: {}".format(operation.operator))
    
    def _optimised_binary_operation(self, operation):
        if (operation.operator in operations.number and
                self._type_of(operation.left) == types.int_type and
                self._type_of(operation.right) == types.int_type):
            return operations.number[operation.operator](
                self.transform(operation.left),
                self.transform(operation.right),
            )
    
    
    def _unary_operation(self, operation):
        if operation.operator == "not":
            return js.unary_operation("!", self.transform(operation.operand))
        else:
            raise Exception("Unrecognised unary operator: {}".format(operation.operator))
    
    def _optimised_unnary_operation(self, operation):
        if (operation.operator in operations.number and
                self._type_of(operation.operand) == types.int_type):
            return operations.number[operation.operator](self.transform(operation.operand))
    
    def _operation(self, operator_name, operands):
        return call_internal(
            ["operators", operator_name],
            [self.transform(operand) for operand in operands],
        )
    
    def _get_magic_method(self, receiver, name):
        # TODO: get magic method through the same mechanism as self._call
        return self._getattr(receiver, "__{}__".format(name))


    def _list_literal(self, node):
        return js.array(self._transform_all(node.elements))
    
    
    def _tuple_literal(self, node):
        elements = js.array(self._transform_all(node.elements))
        return call_internal(["jsArrayToTuple"], [elements])
    
    
    def _getattr(self, value, attr_name):
        return _call_builtin("getattr", [value, js.string(attr_name)])
    
    
    def _get_nope_exception_from_error(self, error):
        return js.property_access(error, "$nopeException")


    def _transform_all(self, nodes):
        return list(filter(None, map(self.transform, nodes)))
    
    
    def _unique_name(self, base):
        name = "${}{}".format(base, self._unique_name_index)
        self._unique_name_index += 1
        return name
    
    def _is_undefined(self, value):
        return js.binary_operation("===", value, js.ref("$nope.undefined"))


def _call_builtin(name, args):
    return call_internal(["builtins", name], args)


def _ref(ref):
    return js.ref(ref.name)


def _internal_ref(ref):
    return js.ref("$nope.{}".format(ref.name))


def _builtin_ref(ref):
    return js.ref("$nope.builtins.{}".format(ref.name))


def _none(none):
    return js.null


def _bool(boolean):
    return js.boolean(boolean.value)


def _int(node):
    return js.number(node.value)


def _str(node):
    return js.string(node.value)
