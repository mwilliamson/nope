import functools

from . import nodes


class Visitor(object):
    def __init__(self):
        self._default_visitors = {
            nodes.NoneExpression: self._visit_nothing,
            nodes.BooleanExpression: self._visit_nothing,
            nodes.IntExpression: self._visit_nothing,
            nodes.StringExpression: self._visit_nothing,
            nodes.VariableReference: self._visit_nothing,
            nodes.TupleLiteral: self._visit_tuple_literal,
            nodes.ListLiteral: self._visit_list_literal,
            nodes.DictLiteral: self._visit_dict_literal,
            nodes.Call: self._visit_call,
            nodes.AttributeAccess: self._visit_attribute_access,
            nodes.UnaryOperation: self._visit_unary_operation,
            nodes.BinaryOperation: self._visit_binary_operation,
            nodes.Subscript: self._visit_subscript,
            nodes.Slice: self._visit_slice,
            
            nodes.ReturnStatement: self._visit_return,
            nodes.ExpressionStatement: self._visit_expression_statement,
            nodes.Assignment: self._visit_assignment,
            nodes.IfElse: self._visit_if_else,
            nodes.WhileLoop: self._visit_while_loop,
            nodes.ForLoop: self._visit_for_loop,
            nodes.BreakStatement: self._visit_nothing,
            nodes.ContinueStatement: self._visit_nothing,
            nodes.TryStatement: self._visit_try,
            nodes.RaiseStatement: self._visit_raise,
            nodes.AssertStatement: self._visit_assert,
            nodes.WithStatement: self._visit_with,
            #~ nodes.FunctionDef: self._visit_function_def,
            nodes.FunctionSignature: self._visit_function_signature,
            nodes.SignatureArgument: self._visit_signature_argument,
            nodes.Argument: self._visit_nothing,
            
            nodes.Import: self._visit_nothing,
            nodes.ImportFrom: self._visit_nothing,
            
            nodes.Module: self._visit_module,
        }
        self._visitors = self._default_visitors.copy()
        self._before = {}
        self._after = {}
    
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
            
        result = self._visitors[node_type](node, *args)
        
        if node_type in self._after:
            self._after[node_type](self, node, *args)
        
        return result

    def _visit_statements(self, statements, *args):
        for statement in statements:
            self.visit(statement, *args)
    
    def _visit_nothing(self, node, *args):
        pass
    
    def _visit_tuple_literal(self, node, *args):
        for element in node.elements:
            self.visit(element, *args)
    
    def _visit_list_literal(self, node, *args):
        for element in node.elements:
            self.visit(element, *args)
    
    def _visit_dict_literal(self, node, *args):
        for key, value in node.items:
            self.visit(key, *args)
            self.visit(value, *args)
    
    def _visit_call(self, node, *args):
        self.visit(node.func, *args)
        for arg in node.args:
            self.visit(arg, *args)
        for arg in node.kwargs.values():
            self.visit(arg, *args)


    def _visit_attribute_access(self, node, *args):
        self.visit(node.value, *args)


    def _visit_unary_operation(self, node, *args):
        self.visit(node.operand, *args)


    def _visit_binary_operation(self, node, *args):
        self.visit(node.left, *args)
        self.visit(node.right, *args)


    def _visit_subscript(self, node, *args):
        self.visit(node.value, *args)
        self.visit(node.slice, *args)


    def _visit_slice(self, node, *args):
        self.visit(node.start, *args)
        self.visit(node.stop, *args)
        self.visit(node.step, *args)


    def _visit_return(self, node, *args):
        if node.value is not None:
            self.visit(node.value, *args)


    def _visit_expression_statement(self, node, *args):
        self.visit(node.value, *args)


    def _visit_assignment(self, node, *args):
        self.visit(node.value, *args)
        
        for target in node.targets:
            self.visit(target, *args)


    def _visit_if_else(self, node, *args):
        self.visit(node.condition, *args)
        
        self._visit_statements(node.true_body, *args)
        self._visit_statements(node.false_body, *args)


    def _visit_while_loop(self, node, *args):
        self.visit(node.condition, *args)
        
        self._visit_statements(node.body, *args)
        self._visit_statements(node.else_body, *args)


    def _visit_for_loop(self, node, *args):
        self.visit(node.iterable, *args)
        self.visit(node.target, *args)
        self._visit_statements(node.body, *args)
        self._visit_statements(node.else_body, *args)


    def _visit_try(self, node, *args):
        self._visit_statements(node.body, *args)
        for handler in node.handlers:
            if handler.type is not None:
                self.visit(handler.type, *args)
            if handler.target is not None:
                self.visit(handler.target, *args)
            self._visit_statements(handler.body, *args)
        self._visit_statements(node.finally_body, *args)


    def _visit_raise(self, node, *args):
        self.visit(node.value, *args)


    def _visit_assert(self, node, *args):
        self.visit(node.condition, *args)
        if node.message is not None:
            self.visit(node.message, *args)
    
    
    def _visit_with(self, node, *args):
        self.visit(node.value, *args)
        if node.target is not None:
            self.visit(node.target, *args)
        self._visit_statements(node.body, *args)
    
    
    def _visit_function_signature(self, node, *args):
        for arg in node.args:
            self.visit(arg, *args)
        
        if node.returns is not None:
            self.visit(node.returns, *args)
    
    
    def _visit_signature_argument(self, node, *args):
        self.visit(node.type, *args)
    
    
    def _visit_module(self, node, *args):
        self._visit_statements(node.body, *args)
