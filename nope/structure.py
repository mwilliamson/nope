from . import nodes


class Scope(object):
    def __init__(self, parent, body):
        self.parent = parent
        self.body = body


def is_scope(node):
    return isinstance(node, Scope)


def children(node):
    return (
        child.body if is_scope(child) else child
        for child in scoped_children(node)
    )


def scoped_children(node):
    return filter(None, _children[type(node)](node))


_children = {
    list: lambda node: node,
    tuple: lambda node: node,
    type({}.values()): lambda node: node,
    
    nodes.NoneLiteral: lambda node: [],
    nodes.BooleanLiteral: lambda node: [],
    nodes.IntLiteral: lambda node: [],
    nodes.StringLiteral: lambda node: [],
    nodes.VariableReference: lambda node: [],
    nodes.TupleLiteral: lambda node: node.elements,
    nodes.ListLiteral: lambda node: node.elements,
    nodes.DictLiteral: lambda node: node.items,
    nodes.Call: lambda node: [node.func, node.args, node.kwargs.values()],
    nodes.AttributeAccess: lambda node: [node.value],
    nodes.TypeApplication: lambda node: [node.generic_type, node.params],
    nodes.TypeUnion: lambda node: node.types,
    nodes.UnaryOperation: lambda node: [node.operand],
    nodes.BinaryOperation: lambda node: [node.left, node.right],
    nodes.Subscript: lambda node: [node.value, node.slice],
    nodes.Slice: lambda node: [node.start, node.stop, node.step],
    nodes.Comprehension: lambda node: [node.iterable, Scope(node, [node.target, node.element])],
    nodes.ComprehensionTarget: lambda node: [node.value],

    nodes.ReturnStatement: lambda node: [node.value],
    nodes.ExpressionStatement: lambda node: [node.value],
    nodes.Assignment: lambda node: [node.value, node.targets],
    nodes.IfElse: lambda node: [node.condition, node.true_body, node.false_body],
    nodes.WhileLoop: lambda node: [node.condition, node.body, node.else_body],
    nodes.ForLoop: lambda node: [node.iterable, node.target, node.body, node.else_body],
    nodes.BreakStatement: lambda node: [],
    nodes.ContinueStatement: lambda node: [],
    nodes.TryStatement: lambda node: [node.body, node.handlers, node.finally_body],
    nodes.ExceptHandler: lambda node: [node.type, node.target, node.body],
    nodes.RaiseStatement: lambda node: [node.value],
    nodes.AssertStatement: lambda node: [node.condition, node.message],
    nodes.WithStatement: lambda node: [node.value, node.target, node.body],
    nodes.FunctionDef: lambda node: [Scope(node, [node.type, node.args, node.body])],
    nodes.Arguments: lambda node: [node.args],
    nodes.FunctionSignature: lambda node: [node.type_params, node.args, node.returns],
    nodes.SignatureArgument: lambda node: [node.type],
    nodes.Argument: lambda node: [],
    nodes.ClassDefinition: lambda node: [node.base_classes, Scope(node, [node.type_params, node.body])],
    nodes.TypeDefinition: lambda node: [node.value],
    nodes.FormalTypeParameter: lambda node: [],
    
    nodes.Import: lambda node: node.names,
    nodes.ImportFrom: lambda node: node.names,
    nodes.ImportAlias: lambda node: [],
    
    nodes.Module: lambda node: [Scope(node, node.body)],
    
    nodes.FieldDefinition: lambda node: [node.name, node.type],
}
