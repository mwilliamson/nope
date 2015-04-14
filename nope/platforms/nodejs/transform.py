import zuice

from ... import nodes, types, couscous as cc
from ...modules import BuiltinModule
from ...module_resolution import ModuleResolver
from ...iterables import find
from . import js, operations
from .internals import call_internal


class NodeTransformer(zuice.Base):
    _module_resolver = zuice.dependency(ModuleResolver)
    
    @zuice.init
    def init(self):
        self._transformers = {
            cc.Module: self._module,
            cc.ModuleReference: self._module_reference,
            
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
            
            cc.FunctionExpression: self._function_expression,
            cc.Call: self._call,
            cc.AttributeAccess: self._attr,
            cc.BinaryOperation: self._binary_operation,
            cc.UnaryOperation: self._unary_operation,
            cc.TernaryConditional: self._ternary_conditional,
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
        if node_type in self._optimised_transformers:
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


    def _module_reference(self, ref):
        return self._import_module_expr(ref.names)


    def _import_module_expr(self, module_name):
        module_path = "/".join(module_name)
        if module_path.endswith("."):
            module_path += "/"
        
        module = self._module_resolver.resolve_import_path(module_name)
        if isinstance(module, BuiltinModule):
            module_path = "__stdlib/{}".format(module_path)
        
        return js.call(js.ref("$require"), [js.string(module_path)])


    def _expression_statement(self, statement):
        return js.expression_statement(self.transform(statement.value))


    def _declare(self, declaration):
        if declaration.value is None:
            return js.var(declaration.name)
        else:
            return js.var(declaration.name, self.transform(declaration.value))


    def _assign(self, assignment):
        value = self.transform(assignment.value)
        
        if isinstance(assignment.target, cc.AttributeAccess):
            target = js.property_access(self.transform(assignment.target.obj), assignment.target.attr)
        else:
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
            init_method = find(lambda method: method.name == "__init__", class_definition.methods)
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
        
        declare_self = js.var(self_name, js.obj({
            "$nopeType": js.ref(class_definition.name)
        }))
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
        return js.if_(
            self.transform(statement.condition),
            self._transform_all(statement.true_body),
            self._transform_all(statement.false_body),
        )
    
    
    def _while_loop(self, loop):
        return js.while_(
            self.transform(loop.condition),
            self._transform_all(loop.body),
        )
    
    
    def _break_statement(self, statement):
        return js.break_
    
    
    def _continue_statement(self, statement):
        return js.continue_


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
                
                js_handler = js.if_(
                    _call_builtin("isinstance", [nope_exception, handler_type]),
                    handler_body,
                    [js_handler],
                )
            
            js_handler = js.if_(
                self._is_undefined(nope_exception),
                [js.throw(js.ref(exception_name))],
                [js_handler],
            )
        else:
            js_handler = None
        
        body = self._transform_all(statement.body)
        finally_body = self._transform_all(statement.finally_body)
        
        if js_handler or finally_body:
            return js.try_(
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
    
    
    def _function_expression(self, function):
        return js.function_expression(
            [arg.name for arg in function.args],
            self._transform_all(function.body)
        )
    
    def _call(self, call):
        args = [self.transform(arg) for arg in call.args]
        return js.call(self.transform(call.func), args)

    def _attr(self, attr):
        return self._getattr(self.transform(attr.obj), attr.attr)
    
    def _binary_operation(self, operation):
        if operation.operator == "and":
            return js.and_(
                self.transform(operation.left),
                self.transform(operation.right),
            )
        elif operation.operator == "or":
            return js.or_(
                self.transform(operation.left),
                self.transform(operation.right),
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

    def _ternary_conditional(self, node):
        return js.ternary_conditional(
            self.transform(node.condition),
            self.transform(node.true_value),
            self.transform(node.false_value),
        )

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
