from nope import nodes, errors


def resolve(node, context):
    return _resolvers[type(node)](node, context)


def _resolve_nothing(node, context):
    pass


def _resolve_variable_reference(node, context):
    if not context.is_defined(node.name):
        raise errors.UndefinedNameError(node, node.name)
    context.add_reference(node)


def _resolve_list_expression(node, context):
    for element in node.elements:
        resolve(element, context)


def _resolve_call(node, context):
    resolve(node.func, context)
    for arg in node.args:
        resolve(arg, context)
    for arg in node.kwargs.values():
        resolve(arg, context)


def _resolve_attribute_access(node, context):
    resolve(node.value, context)


def _resolve_unary_operation(node, context):
    resolve(node.operand, context)


def _resolve_binary_operation(node, context):
    resolve(node.left, context)
    resolve(node.right, context)


def _resolve_subscript(node, context):
    resolve(node.value, context)
    resolve(node.slice, context)


def _resolve_return(node, context):
    if node.value is not None:
        resolve(node.value, context)


def _resolve_expression_statement(node, context):
    resolve(node.value, context)


def _resolve_assignment(node, context):
    resolve(node.value, context)
    
    for target in node.targets:
        if isinstance(target, nodes.VariableReference) and not context.is_defined(target.name):
            context.define(target.name, target)
        
        resolve(target, context)


_resolvers = {
    nodes.NoneExpression: _resolve_nothing,
    nodes.BooleanExpression: _resolve_nothing,
    nodes.IntExpression: _resolve_nothing,
    nodes.StringExpression: _resolve_nothing,
    nodes.VariableReference: _resolve_variable_reference,
    nodes.ListExpression: _resolve_list_expression,
    nodes.Call: _resolve_call,
    nodes.AttributeAccess: _resolve_attribute_access,
    nodes.UnaryOperation: _resolve_unary_operation,
    nodes.BinaryOperation: _resolve_binary_operation,
    nodes.Subscript: _resolve_subscript,
    
    nodes.ReturnStatement: _resolve_return,
    nodes.ExpressionStatement: _resolve_expression_statement,
    
    nodes.Assignment: _resolve_assignment,
}


class Context(object):
    def __init__(self):
        self._definitions = {}
        self._references = {}
    
    def define(self, name, node):
        self._definitions[name] = node
    
    def definition(self, name):
        return self._definitions[name]
    
    def is_defined(self, name):
        return name in self._definitions
    
    def add_reference(self, reference):
        definition = self.definition(reference.name)
        self._references[id(reference)] = definition
    
    def resolve(self, node):
        return self._references[id(node)]
