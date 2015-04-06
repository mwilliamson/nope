import zuice

from nope import nodes, errors, name_declaration, structure, environment
from nope.identity_dict import NodeDict


class NameResolver(zuice.Base):
    _declaration_finder = zuice.dependency(name_declaration.DeclarationFinder)
    _initial_declarations = zuice.dependency(environment.InitialDeclarations)
    
    def resolve(self, node):
        references = NodeDict()
        context = _Context(self._declaration_finder, self._initial_declarations, references)
        _resolve(node, context)
        return References(references)


class References(object):
    def __init__(self, references):
        self._references = NodeDict.create(references)
    
    def referenced_declaration(self, reference):
        return self._references[reference]
    
    def __iter__(self):
        return iter(self._references.keys())


def _resolve(node, context):
    if node is None:
        return
    elif structure.is_scope(node):
        scope_context = context.enter_scope(node)
        _resolve(node.body, scope_context)
    else:
        declared_name = _declared_name(node)
        if declared_name is not None:
            context.add_reference(node, declared_name)
        
        resolver = _resolvers.get(type(node))
        if resolver is not None:
            resolver(node, context)
        else:
            for child in structure.scoped_children(node):
                _resolve(child, context)


_name_declarations = {
    nodes.VariableReference: lambda node: node.name,
    nodes.FunctionDef: lambda node: node.name,
    nodes.ClassDefinition: lambda node: node.name,
    nodes.TypeDefinition: lambda node: node.name,
    nodes.FormalTypeParameter: lambda node: node.name,
    nodes.ImportAlias: lambda node: node.value_name,
}

def _declared_name(node):
    return _name_declarations.get(type(node), lambda node: None)(node)


def _resolve_named_node(node, context):
    context.add_reference(node, node.name)


def _resolve_comprehension(node, context):
    _resolve(node.body.iterable, context)
    
    body_context = context.enter_comprehension(node)
    _resolve(node.body.target, body_context)
    _resolve(node.body.element, body_context)


def _resolve_function_def(node, context):
    context.add_reference(node, node.name)
    
    body_context = context.enter_function(node)
    
    _resolve(node.type, body_context)
    
    for arg in node.args.args:
        _resolve(arg, body_context)
        body_context.add_reference(arg, arg.name)
    
    for statement in node.body:
        _resolve(statement, body_context)


_resolvers = {
    nodes.ListComprehension: _resolve_comprehension,
    nodes.FunctionDef: _resolve_function_def,
}


class _Context(object):
    def __init__(self, declaration_finder, declarations, references, declarations_for_functions=None):
        assert isinstance(references, NodeDict)
        
        if declarations_for_functions is None:
            declarations_for_functions = declarations
        
        self._declaration_finder = declaration_finder
        self._declarations = declarations
        self._declarations_for_functions = declarations_for_functions
        self._references = references
    
    def is_declared(self, name):
        return self._declarations.is_declared(name)
    
    def add_reference(self, reference, name):
        if not self.is_declared(name):
            raise errors.UndefinedNameError(reference, name)
            
        self._references[reference] = self._declarations.declaration(name)
    
    def enter_function(self, node):
        function_declarations = self._declaration_finder.declarations_in(node)
        declarations = self._declarations_for_functions.enter(function_declarations)
        # TODO: tidy up this hack.
        for declaration in self._declarations:
            if isinstance(declaration, (name_declaration.TypeDeclarationNode, name_declaration.SelfTypeDeclarationNode)):
                declarations._declarations[declaration.name] = declaration
        return _Context(self._declaration_finder, declarations, self._references)
    
    def enter_scope(self, scope):
        declarations_in_scope = self._declaration_finder.declarations_in(scope.parent)
        declarations_for_scope = self._declarations.enter(declarations_in_scope)
        
        return _Context(
            declaration_finder=self._declaration_finder,
            declarations=declarations_for_scope,
            references=self._references,
            declarations_for_functions=self._declarations_for_functions_in_scope(scope, declarations_for_scope),
        )
    
    def _declarations_for_functions_in_scope(self, scope, declarations_for_scope):
        if isinstance(scope.parent, nodes.Module):
            return declarations_for_scope
        elif isinstance(scope.parent, nodes.ClassDefinition):
            return self._declarations
        else:
            raise Exception("Unhandled case")
    
    def enter_comprehension(self, node):
        comprehension_declarations = self._declaration_finder.declarations_in(node)
        declarations = self._declarations.enter(comprehension_declarations)
        return _Context(self._declaration_finder, declarations, self._references, declarations_for_functions=self._declarations_for_functions)
