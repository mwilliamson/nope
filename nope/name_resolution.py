from nope import nodes, errors, name_declaration, visit
from nope.identity_dict import IdentityDict


class NameResolver(object):
    def __init__(self, declaration_finder):
        self._declaration_finder = declaration_finder
    
    def resolve(self, node, declarations, references=None):
        if references is None:
            references = IdentityDict()
        context = _Context(self._declaration_finder, declarations, references)
        _resolve(node, context)
        return References(references)


class References(object):
    def __init__(self, references):
        self._references = IdentityDict.create(references)
    
    def referenced_declaration(self, reference):
        return self._references[reference]


def _resolve(node, context):
    visitor = visit.Visitor()
    visitor.replace(nodes.VariableReference, _resolve_variable_reference)
    visitor.replace(nodes.FunctionDef, _resolve_function_def)
    visitor.replace(nodes.ClassDefinition, _resolve_class_definition)
    visitor.replace(nodes.Import, _resolve_import)
    visitor.replace(nodes.ImportFrom, _resolve_import)
    visitor.replace(nodes.Module, _resolve_module)
    
    return visitor.visit(node, context)


def _resolve_variable_reference(visitor, node, context):
    if not context.is_declared(node.name):
        raise errors.UndefinedNameError(node, node.name)
    
    context.add_reference(node, node.name)


def _resolve_function_def(visitor, node, context):
    context.add_reference(node, node.name)
    
    if node.signature is not None:
        visitor.visit(node.signature, context)
    
    body_context = context.enter_function(node)
    for arg in node.args.args:
        body_context.add_reference(arg, arg.name)
    
    for statement in node.body:
        visitor.visit(statement, body_context)


def _resolve_class_definition(visitor, node, context):
    context.add_reference(node, node.name)
    
    body_context = context.enter_class(node)
    
    for statement in node.body:
        visitor.visit(statement, body_context)


def _resolve_import(visitor, node, context):
    for alias in node.names:
        context.add_reference(alias, alias.value_name)


def _resolve_module(visitor, node, context):
    module_context = context.enter_module(node)
    
    for statement in node.body:
        visitor.visit(statement, module_context)


class _Context(object):
    def __init__(self, declaration_finder, declarations, references, declarations_for_functions=None):
        assert isinstance(references, IdentityDict)
        
        if declarations_for_functions is None:
            declarations_for_functions = declarations
        
        self._declaration_finder = declaration_finder
        self._declarations = declarations
        self._declarations_for_functions = declarations_for_functions
        self._references = references
    
    def is_declared(self, name):
        return self._declarations.is_declared(name)
    
    def add_reference(self, reference, name):
        self._references[reference] = self._declarations.declaration(name)
    
    def enter_function(self, node):
        function_declarations = self._declaration_finder.declarations_in_function(node)
        declarations = self._declarations_for_functions.enter(function_declarations)
        return _Context(self._declaration_finder, declarations, self._references)
    
    def enter_class(self, node):
        class_declarations = self._declaration_finder.declarations_in_class(node)
        declarations = self._declarations.enter(class_declarations)
        return _Context(self._declaration_finder, declarations, self._references, declarations_for_functions=self._declarations)
    
    def enter_module(self, node):
        module_declarations = self._declaration_finder.declarations_in_module(node)
        declarations = self._declarations.enter(module_declarations)
        return _Context(self._declaration_finder, declarations, self._references)
