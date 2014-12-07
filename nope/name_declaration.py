from nope import nodes, errors, visit
from nope.identity_dict import IdentityDict


def _declare(node, declarations):
    visitor = visit.Visitor()
    visitor.before(nodes.Assignment, _declare_assignment)
    visitor.before(nodes.ForLoop, _declare_for_loop)
    visitor.before(nodes.TryStatement, _declare_try)
    visitor.before(nodes.WithStatement, _declare_with)
    visitor.replace(nodes.FunctionDef, _declare_function_def)
    visitor.replace(nodes.ClassDefinition, _declare_class_definition)
    visitor.before(nodes.TypeDefinition, _declare_type_definition)
    visitor.before(nodes.Argument, _declare_argument)
    visitor.before(nodes.Import, _declare_import)
    visitor.before(nodes.ImportFrom, _declare_import)
    
    return visitor.visit(node, declarations)


def _declare_target(target, declarations, target_type):
    if isinstance(target, nodes.VariableReference):
        declarations.declare(target.name, target, target_type=target_type)
    elif isinstance(target, nodes.TupleLiteral):
        for element in target.elements:
            _declare_target(element, declarations, target_type)


def _declare_assignment(visitor, node, declarations):
    for target in node.targets:
        _declare_target(target, declarations, target_type=VariableDeclarationNode)


def _declare_for_loop(visitor, node, declarations):
    _declare_target(node.target, declarations, target_type=VariableDeclarationNode)


def _declare_try(visitor, node, declarations):
    for handler in node.handlers:
        if handler.target is not None:
            _declare_target(handler.target, declarations, target_type=ExceptionHandlerTargetNode)


def _declare_with(visitor, node, declarations):
    if node.target is not None:
        _declare_target(node.target, declarations, target_type=VariableDeclarationNode)


def _declare_function_def(visitor, node, declarations):
    declarations.declare(node.name, node, target_type=FunctionDeclarationNode)


def _declare_class_definition(visitor, node, declarations):
    declarations.declare(node.name, node, target_type=ClassDeclarationNode)


def _declare_type_definition(visitor, node, declarations):
    declarations.declare(node.name, node, target_type=TypeDeclarationNode)


def _declare_argument(visitor, node, declarations):
    declarations.declare(node.name, node, target_type=VariableDeclarationNode)


def _declare_import(visitor, node, declarations):
    for alias in node.names:
        declarations.declare(alias.value_name, alias, target_type=ImportDeclarationNode)


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



class VariableDeclarationNode(object):
    description = "variable assignment"
    
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return "VariableDeclarationNode({})".format(self.name)


class ExceptionHandlerTargetNode(object):
    description = "exception handler target"
    
    def __init__(self, name):
        self.name = name


class FunctionDeclarationNode(object):
    description = "function declaration"
    
    def __init__(self, name):
        self.name = name


class ClassDeclarationNode(object):
    description = "class declaration"
    
    def __init__(self, name):
        self.name = name


class TypeDeclarationNode(object):
    description = "type declaration"
    
    def __init__(self, name):
        self.name = name


class SelfTypeDeclarationNode(object):
    description = "self type declaration"
    
    def __init__(self, name):
        self.name = name


class ImportDeclarationNode(object):
    description = "import statement"
    
    def __init__(self, name):
        self.name = name



class DeclarationFinder(object):
    def __init__(self):
        self._node_to_declarations = IdentityDict()

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
    
    for arg in node.args.args:
        _declare(arg, declarations)
    
    for statement in node.body:
        _declare(statement, declarations)
        
    return declarations
        
        
def _declarations_in_class(node):
    declarations = Declarations({})
    
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
    _declare_target(node.target, declarations, target_type=VariableDeclarationNode)
    return declarations
