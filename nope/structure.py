from . import nodes, types


class Scope(object):
    def __init__(self, parent, body):
        self.parent = parent
        self.body = body


def is_scope(node):
    return isinstance(node, Scope)


class Branch(object):
    def __init__(self, body):
        self.body = filter(None, body)


class ExhaustiveBranches(object):
    def __init__(self, branches):
        self.branches = branches


class Delete(object):
    def __init__(self, target):
        self.target = target


def children(node, type_lookup=None):
    return (
        child.body if is_scope(child) else child
        for child in scoped_children(node, type_lookup)
    )


def descendants(node):
    for child in children(node):
        yield child
        yield from descendants(child)


def scoped_children(node, type_lookup=None):
    if isinstance(node, nodes.WithStatement):
        return _with_statement(node, type_lookup)
    else:
        return filter(None, _children[type(node)](node))


_children = {
    list: lambda node: node,
    tuple: lambda node: node,
    type({}.values()): lambda node: node,
    Branch: lambda node: node.body,
    ExhaustiveBranches: lambda node: node.branches,
    Delete: lambda node: [node.target],
    
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
    nodes.Comprehension: lambda node: [node.iterable, Scope(node, [nodes.Target(node.target), node.element])],
    nodes.Target: lambda node: [node.value],

    nodes.ReturnStatement: lambda node: [node.value],
    nodes.ExpressionStatement: lambda node: [node.value],
    nodes.Assignment: lambda node: [node.type, node.value, list(map(nodes.Target, node.targets))],
    
    nodes.IfElse: lambda node: [node.condition, ExhaustiveBranches([node.true_body, node.false_body])],
    
    nodes.WhileLoop: lambda node: [node.condition, Branch(node.body), Branch(node.else_body)],
    
    nodes.ForLoop: lambda node: [
        node.iterable,
        Branch([nodes.Target(node.target), node.body]),
        Branch(node.else_body),
    ],
    
    nodes.BreakStatement: lambda node: [],
    nodes.ContinueStatement: lambda node: [],
    nodes.TryStatement: lambda node: [Branch(node.body), node.handlers, Branch(node.finally_body)],
    
    nodes.ExceptHandler: lambda node: [
        node.type,
        Branch(node.body if node.target is None else [nodes.Target(node.target), node.body, Delete(node.target)]),
    ],
    
    nodes.RaiseStatement: lambda node: [node.value],
    nodes.AssertStatement: lambda node: [node.condition, node.message],
    nodes.FunctionDef: lambda node: [Scope(node, [node.type, node.args, node.body])],
    nodes.Arguments: lambda node: [node.args],
    nodes.FunctionSignature: lambda node: [node.type_params, node.args, node.returns],
    nodes.SignatureArgument: lambda node: [node.type],
    nodes.Argument: lambda node: [],
    nodes.ClassDefinition: lambda node: [node.base_classes, Scope(node, [node.type_params, node.body])],
    nodes.TypeDefinition: lambda node: [node.value],
    nodes.StructuralTypeDefinition: lambda node: [attr[1] for attr in node.attrs],
    nodes.FormalTypeParameter: lambda node: [],
    
    nodes.Import: lambda node: node.names,
    nodes.ImportFrom: lambda node: node.names,
    nodes.ImportAlias: lambda node: [],
    
    nodes.Module: lambda node: [Scope(node, node.body)],
    
    nodes.FieldDefinition: lambda node: [node.name, node.type],
}

def _with_statement(node, type_lookup):
    if node.target is None:
        body_nodes = node.body
    else:
        body_nodes = [nodes.Target(node.target), node.body]

    if _exit_type_is_none(node, type_lookup):
        body = ExhaustiveBranches([body_nodes])
    else:
        body = Branch(body_nodes)
    
    return [node.value, body]

def _exit_type_is_none(node, type_lookup):
    if type_lookup is None:
        return False
    
    value_type = type_lookup.type_of(node.value)
    if value_type is None:
        return False
    
    exit_type = value_type.attrs.type_of("__exit__")
    # TODO: this is duplicated in codegeneration
    while not types.is_func_type(exit_type):
        exit_type = exit_type.attrs.type_of("__call__")
    
    return exit_type.return_type == types.none_type
