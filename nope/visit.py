import functools

from . import nodes


class Visitor(object):
    def __init__(self, visit_explicit_types=True):
        self._default_visitors = {
            nodes.NoneLiteral: self._visit_nothing,
            nodes.BooleanLiteral: self._visit_nothing,
            nodes.IntLiteral: self._visit_nothing,
            nodes.StringLiteral: self._visit_nothing,
            nodes.VariableReference: self._visit_nothing,
            nodes.TupleLiteral: self._visit_tuple_literal,
            nodes.ListLiteral: self._visit_list_literal,
            nodes.DictLiteral: self._visit_dict_literal,
            nodes.Call: self._visit_call,
            nodes.AttributeAccess: self._visit_attribute_access,
            nodes.TypeApplication: self._visit_type_application,
            nodes.TypeUnion: self._visit_type_union,
            nodes.UnaryOperation: self._visit_unary_operation,
            nodes.BinaryOperation: self._visit_binary_operation,
            nodes.Subscript: self._visit_subscript,
            nodes.Slice: self._visit_slice,
            nodes.ListComprehension: self._visit_comprehension,
            nodes.GeneratorExpression: self._visit_comprehension,
            nodes.Comprehension: self._visit_comprehension_generator,
            
            nodes.ReturnStatement: self._visit_return,
            nodes.ExpressionStatement: self._visit_expression_statement,
            nodes.Assignment: self._visit_assignment,
            nodes.IfElse: self._visit_if_else,
            nodes.WhileLoop: self._visit_while_loop,
            nodes.ForLoop: self._visit_for_loop,
            nodes.BreakStatement: self._visit_nothing,
            nodes.ContinueStatement: self._visit_nothing,
            nodes.TryStatement: self._visit_try,
            nodes.ExceptHandler: self._visit_except_handler,
            nodes.RaiseStatement: self._visit_raise,
            nodes.AssertStatement: self._visit_assert,
            nodes.WithStatement: self._visit_with,
            nodes.FunctionDef: self._visit_function_def,
            nodes.Arguments: self._visit_arguments,
            nodes.FunctionSignature: self._visit_function_signature,
            nodes.SignatureArgument: self._visit_signature_argument,
            nodes.Argument: self._visit_argument,
            nodes.ClassDefinition: self._visit_class_definition,
            nodes.TypeDefinition: self._visit_type_definition,
            
            nodes.Import: self._visit_nothing,
            nodes.ImportFrom: self._visit_nothing,
            
            nodes.Module: self._visit_module,
            
            type(None): lambda *args: None
        }
        self._visitors = self._default_visitors.copy()
        self._before = {}
        self._after = {}
        if visit_explicit_types:
            self.visit_explicit_type = self.visit
        else:
            self.visit_explicit_type = lambda node, *args: node
    
    def replace(self, node_type, func):
        self._visitors[node_type] = functools.partial(func, self)
    
    def before(self, node_type, func):
        self._before[node_type] = func
    
    def after(self, node_type, func):
        self._after[node_type] = func
    
    def visit(self, node, *args):
        node_type = type(node)
        
        if node_type in self._before:
            self._before[node_type](self, node, *args)
        
        explicit_type = nodes.explicit_type_of(node)
        if explicit_type is None:
            explicit_type_result = None
        else:
            explicit_type_result = self.visit_explicit_type(explicit_type, *args)
            
        result = self._visitors[node_type](node, *args)
        
        if result is not None and getattr(result, "location", None) is None and hasattr(node, "location"):
            result.location = node.location
        
        if explicit_type_result is not None and result is not None:
            result = nodes.typed(explicit_type_result, result)
        
        if node_type in self._after:
            self._after[node_type](self, node, *args)
        
        return result

    
    def _visit_statements(self, statements, *args):
        return self._visit_all(statements, *args)
    
    def _visit_all(self, nodes, *args):
        return [self.visit(node, *args) for node in nodes]
    
    def _visit_nothing(self, node, *args):
        return node
    
    def _visit_tuple_literal(self, node, *args):
        return nodes.tuple_literal(self._visit_all(node.elements, *args))
    
    def _visit_list_literal(self, node, *args):
        return nodes.list_literal(self._visit_all(node.elements, *args))
    
    def _visit_dict_literal(self, node, *args):
        return nodes.dict_literal([
            (self.visit(key, *args), self.visit(value, *args))
            for key, value in node.items
        ])
    
    def _visit_call(self, node, *args):
        return nodes.call(
            self.visit(node.func, *args),
            self._visit_all(node.args, *args),
            dict((name, self.visit(value, *args)) for name, value in node.kwargs.items()),
        )

    def _visit_attribute_access(self, node, *args):
        return nodes.attr(self.visit(node.value, *args), node.attr)

    def _visit_type_application(self, node, *args):
        return nodes.type_apply(
            self.visit(node.generic_type, *args),
            self._visit_all(node.params, *args),
        )
    
    def _visit_type_union(self, node, *args):
        return nodes.type_union(self._visit_all(node.types, *args))

    def _visit_unary_operation(self, node, *args):
        return nodes.unary_operation(
            node.operator,
            self.visit(node.operand, *args)
        )

    def _visit_binary_operation(self, node, *args):
        return nodes.binary_operation(
            node.operator,
            self.visit(node.left, *args),
            self.visit(node.right, *args),
        )

    def _visit_subscript(self, node, *args):
        return nodes.subscript(
            self.visit(node.value, *args),
            self.visit(node.slice, *args),
        )

    def _visit_slice(self, node, *args):
        return nodes.slice(
            self.visit(node.start, *args),
            self.visit(node.stop, *args),
            self.visit(node.step, *args),
        )

    def _visit_comprehension(self, node, *args):
        generator = self.visit(node.generator, *args)
        element = self.visit(node.element, *args)
        return type(node)(element, generator)
    
    def _visit_comprehension_generator(self, node, *args):
        iterable = self.visit(node.iterable, *args)
        target = self.visit(node.target, *args)
        return nodes.comprehension(target, iterable)

    def _visit_return(self, node, *args):
        return nodes.ret(self.visit(node.value, *args))

    def _visit_expression_statement(self, node, *args):
        return nodes.expression_statement(self.visit(node.value, *args))

    def _visit_assignment(self, node, *args):
        value = self.visit(node.value, *args)
        targets = self._visit_all(node.targets, *args)
        return nodes.assign(targets, value)

    def _visit_if_else(self, node, *args):
        return nodes.if_else(
            self.visit(node.condition, *args),
            self._visit_statements(node.true_body, *args),
            self._visit_statements(node.false_body, *args),
        )

    def _visit_while_loop(self, node, *args):
        return nodes.while_loop(
            self.visit(node.condition, *args),
            self._visit_statements(node.body, *args),
            self._visit_statements(node.else_body, *args),
        )

    def _visit_for_loop(self, node, *args):
        iterable = self.visit(node.iterable, *args)
        target = self.visit(node.target, *args)
        return nodes.for_loop(
            target,
            iterable,
            self._visit_statements(node.body, *args),
            self._visit_statements(node.else_body, *args),
        )

    def _visit_try(self, node, *args):
        return nodes.try_statement(
            self._visit_statements(node.body, *args),
            handlers=self._visit_all(node.handlers, *args),
            finally_body=self._visit_all(node.finally_body, *args),
        )

    def _visit_except_handler(self, node, *args):
        return nodes.except_handler(
            self.visit(node.type, *args),
            self.visit(node.target, *args),
            self._visit_statements(node.body, *args),
        )

    def _visit_raise(self, node, *args):
        return nodes.raise_statement(self.visit(node.value, *args))

    def _visit_assert(self, node, *args):
        return nodes.assert_statement(
            self.visit(node.condition, *args),
            self.visit(node.message, *args),
        )
    
    def _visit_with(self, node, *args):
        return nodes.with_statement(
            self.visit(node.value, *args),
            self.visit(node.target, *args),
            self._visit_statements(node.body, *args),
        )
    
    def _visit_function_def(self, node, *args):
        return nodes.func(
            node.name,
            self.visit(node.args, *args),
            self._visit_statements(node.body, *args),
        )
    
    def _visit_arguments(self, node, *args):
        return nodes.arguments(self._visit_all(node.args, *args))
    
    def _visit_function_signature(self, node, *args):
        return nodes.signature(
            args=self._visit_all(node.args, *args),
            returns=self.visit(node.returns, *args)
        )
    
    def _visit_signature_argument(self, node, *args):
        return nodes.signature_arg(node.name, self.visit(node.type, *args), optional=node.optional)
    
    def _visit_argument(self, node, *args):
        return nodes.arg(node.name, optional=node.optional)
    
    def _visit_class_definition(self, node, *args):
        base_classes = self._visit_all(node.base_classes, *args)
        return nodes.class_def(
            node.name,
            self._visit_statements(node.body, *args),
            base_classes=base_classes,
        )
    
    def _visit_type_definition(self, node, *args):
        return nodes.type_definition(node.name, self.visit(node.value, *args))
    
    def _visit_module(self, node, *args):
        return nodes.module(
            self._visit_statements(node.body, *args),
            is_executable=node.is_executable,
        )
        
