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
    
    resolver = _resolvers.get(type(node))
    if resolver is not None:
        resolver(node, context)
    else:
        for child in structure.children(node):
            _resolve(child, context)


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


def _resolve_class_definition(node, context):
    for base_class in node.base_classes:
        _resolve(base_class, context)
    
    context.add_reference(node, node.name)
    
    body_context = context.enter_class(node)
    
    for type_param in node.type_params:
        _resolve(type_param, body_context)
    
    for statement in node.body:
        _resolve(statement, body_context)


def _resolve_import(node, context):
    for alias in node.names:
        context.add_reference(alias, alias.value_name)


def _resolve_module(node, context):
    module_context = context.enter_module(node)
    
    for statement in node.body:
        _resolve(statement, module_context)


def _resolve_type_definition(node, context):
    _resolve_named_node(node, context)
    
    for child in structure.children(node):
        _resolve(child, context)


_resolvers = {
    nodes.VariableReference: _resolve_named_node,
    nodes.ListComprehension: _resolve_comprehension,
    nodes.FunctionDef: _resolve_function_def,
    nodes.TypeDefinition: _resolve_type_definition,
    nodes.FormalTypeParameter: _resolve_named_node,
    nodes.ClassDefinition: _resolve_class_definition,
    nodes.Import: _resolve_import,
    nodes.ImportFrom: _resolve_import,
    nodes.Module: _resolve_module,
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
    
    def enter_class(self, node):
        class_declarations = self._declaration_finder.declarations_in(node)
        declarations = self._declarations.enter(class_declarations)
        return _Context(self._declaration_finder, declarations, self._references, declarations_for_functions=self._declarations)
    
    def enter_module(self, node):
        module_declarations = self._declaration_finder.declarations_in(node)
        declarations = self._declarations.enter(module_declarations)
        return _Context(self._declaration_finder, declarations, self._references)
    
    def enter_comprehension(self, node):
        comprehension_declarations = self._declaration_finder.declarations_in(node)
        declarations = self._declarations.enter(comprehension_declarations)
        return _Context(self._declaration_finder, declarations, self._references, declarations_for_functions=self._declarations_for_functions)
