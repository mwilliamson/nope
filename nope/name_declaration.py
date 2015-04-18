from . import nodes, errors, structure
from .identity_dict import ComputedNodeDict


def _declare(node, declarations):
    _declare_targets(node, declarations)
    _declare_children(node, declarations)


def _declare_targets(node, declarations):
    targets, target_type = _targets(node)
    for target_node, target_name in targets:
        declarations.declare(target_name, target_node, target_type=target_type)


def _declare_children(node, declarations):
    for child in structure.scoped_children(node):
        if not structure.is_scope(child):
            _declare(child, declarations)


def _targets(node):
    if isinstance(node, nodes.Target):
        return _left_value_to_targets(node.value), VariableDeclarationNode
    elif type(node) in _declaration_nodes:
        return [(node, node.name)], _declaration_nodes[type(node)]
    else:
        return [], None
    find_targets, target_type = _targets_of.get(type(node), (lambda node: [], None))
    return find_targets(node), target_type


def _left_values_to_targets(nodes):
    for node in nodes:
        yield from _left_value_to_targets(node)

def _left_value_to_targets(root):
    def generate(node):
        if isinstance(node, nodes.VariableReference):
            yield node
        elif isinstance(node, nodes.TupleLiteral):
            for element in node.elements:
                yield from generate(element)
        
    return ((node, node.name) for node in generate(root))


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
    

VariableDeclarationNode = _create_declaration_node("VariableDeclarationNode", "variable assignment")
FunctionDeclarationNode = _create_declaration_node("FunctionDeclarationNode", "function declaration")
ClassDeclarationNode = _create_declaration_node("ClassDeclarationNode", "class declaration")
TypeDeclarationNode = _create_declaration_node("TypeDeclarationNode", "type declaration")
SelfTypeDeclarationNode = _create_declaration_node("SelfTypeDeclarationNode", "self type declaration")
ImportDeclarationNode = _create_declaration_node("ImportDeclarationNode", "import statement")


class DeclarationFinder(object):
    def __init__(self):
        self._node_to_declarations = ComputedNodeDict(self._generate_declarations)

    def declarations_in(self, node):
        return self._node_to_declarations[node]
        

    def _generate_declarations(self, node):
        declarations = Declarations({})
        
        if isinstance(node, nodes.ClassDefinition):
            declarations.declare("Self", node, target_type=SelfTypeDeclarationNode)
        
        for child in structure.children(node):
            _declare(child, declarations)
            
        return declarations


_declaration_nodes = {
    nodes.FunctionDef: FunctionDeclarationNode,
    nodes.ClassDefinition: ClassDeclarationNode,
    nodes.TypeDefinition: TypeDeclarationNode,
    nodes.StructuralTypeDefinition: TypeDeclarationNode,
    nodes.FormalTypeParameter: TypeDeclarationNode,
    nodes.Argument: VariableDeclarationNode,
    nodes.ImportAlias: ImportDeclarationNode,
}

def declaration_type(node):
    return _declaration_nodes.get(type(node))
