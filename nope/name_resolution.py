import zuice

from nope import nodes, errors, name_declaration, structure, environment
from nope.identity_dict import NodeDict
from .dispatch import TypeDispatch


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
        if name_declaration.declaration_type(node) is not None or isinstance(node, nodes.VariableReference):
            context.add_reference(node, node.name)
        
        for child in structure.scoped_children(node):
            _resolve(child, context)


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
    
    def enter_scope(self, scope):
        declarations_for_scope = self._declarations_for_scope(scope)
        
        return _Context(
            declaration_finder=self._declaration_finder,
            declarations=declarations_for_scope,
            references=self._references,
            declarations_for_functions=self._declarations_for_functions_in_scope(scope, declarations_for_scope),
        )
    
    def _declarations_for_scope(self, scope):
        declarations_in_scope = self._declaration_finder.declarations_in(scope.parent)
        if isinstance(scope.parent, nodes.FunctionDef):
            declarations = self._declarations_for_functions.enter(declarations_in_scope)
            # TODO: tidy up this hack. This allows type parameters (on generic classes)
            # and the Self type to be accessed in methods
            for declaration in self._declarations:
                if isinstance(declaration, (name_declaration.TypeDeclarationNode, name_declaration.SelfTypeDeclarationNode)):
                    declarations._declarations[declaration.name] = declaration
            return declarations
        else:
            return self._declarations.enter(declarations_in_scope)
    
    def _declarations_for_functions_in_scope(self, scope, declarations_for_scope):
        if isinstance(scope.parent, nodes.Module):
            return declarations_for_scope
        elif isinstance(scope.parent, nodes.ClassDefinition):
            return self._declarations
        elif isinstance(scope.parent, nodes.Comprehension):
            return self._declarations_for_functions
        elif isinstance(scope.parent, nodes.FunctionDef):
            return None
        else:
            raise Exception("Unhandled case")
