from . import nodes, errors, structure
from .identity_dict import NodeDict


def _declare(node, declarations):
    targets, target_type = _targets(node)
    _declare_targets(targets, target_type, declarations)
    
    if not _creates_new_scope(node):
        _declare_children(node, declarations)


def _declare_targets(targets, target_type, declarations):
    for target_node, target_name in targets:
        declarations.declare(target_name, target_node, target_type=target_type)


def _creates_new_scope(node):
    return isinstance(node, (nodes.FunctionDef, nodes.ClassDefinition))


def _declare_children(node, declarations):
    for child in structure.children(node):
        _declare(child, declarations)


def _targets(node):
    left_values, target_type = _left_values(node)
    if target_type is not None:
        targets = []
        for left_value in left_values:
            _left_value_to_targets(left_value, targets)
        
        return targets, target_type
    else:
        return _targets_of.get(type(node), lambda node: ([], None))(node)


_targets_of = {
    nodes.FunctionDef: lambda node: ([(node, node.name)], FunctionDeclarationNode),
    nodes.ClassDefinition: lambda node: ([(node, node.name)], ClassDeclarationNode),
    nodes.TypeDefinition: lambda node: ([(node, node.name)], TypeDeclarationNode),
    nodes.FormalTypeParameter: lambda node: ([(node, node.name)], TypeDeclarationNode),
    nodes.Argument: lambda node: ([(node, node.name)], VariableDeclarationNode),
    nodes.ImportAlias: lambda node: ([(node, node.value_name)], ImportDeclarationNode),
}


def _left_value_to_targets(left_value, targets):
    if isinstance(left_value, nodes.VariableReference):
        targets.append((left_value, left_value.name))
    elif isinstance(left_value, nodes.TupleLiteral):
        for child in left_value.elements:
            _left_value_to_targets(child, targets)
    


def _left_values(node):
    left_values_of = _left_values_of.get(type(node), lambda node: ([], None))
    return left_values_of(node)

_left_values_of = {
    nodes.Assignment: lambda node: (node.targets, VariableDeclarationNode),
    nodes.ForLoop: lambda node: ([node.target], VariableDeclarationNode),
    nodes.ExceptHandler: lambda node: (filter(None, [node.target]), ExceptionHandlerTargetNode),
    nodes.WithStatement: lambda node: (filter(None, [node.target]), VariableDeclarationNode),
}


class Declarations(object):
    def __init__(self, declarations):
        self._declarations = declarations
    
    def names(self):
        return self._declarations.keys()
    
    def declare(self, name, target_node, target_type):
        if name in self._declarations:
            declaration_node = self._declarations[name]
            node_type = type(declaration_node)
            if node_type != target_type:
                raise errors.InvalidReassignmentError(
                    target_node,
                    "{} and {} cannot share the same name".format(target_type.description, node_type.description)
                )
        else:
            declaration_node = self._declarations[name] = target_type(name)
        
        return declaration_node
    
    def declaration(self, name):
        return self._declarations[name]
    
    def is_declared(self, name):
        return name in self._declarations
    
    def enter(self, new_declarations):
        declarations = self._declarations.copy()
        declarations.update(new_declarations._declarations)
        return Declarations(declarations)
    
    def __iter__(self):
        return iter(self._declarations.values())
    
    def __repr__(self):
        return "Declarations({})".format(self._declarations)



def _create_declaration_node(node_type_name, node_type_description):
    class Node(object):
        description = node_type_description
        
        def __init__(self, name):
            self.name = name
        
        def __repr__(self):
            return "{}({})".format(node_type_name, self.name)
    
    Node.__name__ = node_type_name
    return Node
    

VariableDeclarationNode = _create_declaration_node("VariableDeclaratioNode", "variable assignment")
ExceptionHandlerTargetNode = _create_declaration_node("ExceptionHandlerTargetNode", "exception handler target")
FunctionDeclarationNode = _create_declaration_node("FunctionDeclarationNode", "function declaration")
ClassDeclarationNode = _create_declaration_node("ClassDeclarationNode", "class declaration")
TypeDeclarationNode = _create_declaration_node("TypeDeclarationNode", "type declaration")
SelfTypeDeclarationNode = _create_declaration_node("SelfTypeDeclarationNode", "self type declaration")
ImportDeclarationNode = _create_declaration_node("ImportDeclarationNode", "import statement")


class DeclarationFinder(object):
    def __init__(self):
        self._node_to_declarations = NodeDict()

    def declarations_in_function(self, node):
        return self._declarations(node, _declarations_in_function)

    def declarations_in_class(self, node):
        return self._declarations(node, _declarations_in_class)
        
    def declarations_in_module(self, node):
        return self._declarations(node, _declarations_in_module)
    
    def declarations_in_comprehension(self, node):
        return self._declarations(node, _declarations_in_comprehension)
    
    def _declarations(self, node, generator):
        if node not in self._node_to_declarations:
            self._node_to_declarations[node] = generator(node)
        
        return self._node_to_declarations[node]
        
        
def _declarations_in_function(node):
    declarations = Declarations({})
    
    if isinstance(node.type, nodes.FunctionSignature):
        for param in node.type.type_params:
            _declare(param, declarations)
    
    for arg in node.args.args:
        _declare(arg, declarations)
    
    for statement in node.body:
        _declare(statement, declarations)
        
    return declarations
        
        
def _declarations_in_class(node):
    declarations = Declarations({})
    
    for type_param in node.type_params:
        _declare(type_param, declarations)
    
    declarations.declare("Self", node, target_type=SelfTypeDeclarationNode)
    
    for statement in node.body:
        _declare(statement, declarations)
        
    return declarations


def _declarations_in_module(node):
    declarations = Declarations({})
    
    for statement in node.body:
        _declare(statement, declarations)
        
    return declarations


def _declarations_in_comprehension(node):
    declarations = Declarations({})
    targets = []
    _left_value_to_targets(node.target, targets)
    _declare_targets(targets, VariableDeclarationNode, declarations)
    return declarations
