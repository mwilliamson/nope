from nope import nodes, errors, name_declaration, visit
from nope.identity_dict import IdentityDict


def resolve(node, context):
    visitor = visit.Visitor()
    visitor.replace(nodes.VariableReference, _resolve_variable_reference)
    visitor.replace(nodes.FunctionDef, _resolve_function_def)
    visitor.replace(nodes.Import, _resolve_import)
    visitor.replace(nodes.ImportFrom, _resolve_import)
    visitor.replace(nodes.Module, _resolve_module)
    
    return visitor.visit(node, context)


def _resolve_variable_reference(visitor, node, context):
    if not context.is_defined(node.name):
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


def _resolve_import(visitor, node, context):
    for alias in node.names:
        context.add_reference(alias, alias.value_name)


def _resolve_module(visitor, node, context):
    module_context = context.enter_module(node)
    
    for statement in node.body:
        visitor.visit(statement, module_context)
    
    return module_context


class Context(object):
    def __init__(self, declarations, references):
        assert isinstance(references, IdentityDict)
        
        self._declarations = declarations
        self._references = references
    
    # TODO: rename definition to declaration
    def definition(self, name):
        return self._declarations[name]

    def is_defined(self, name):
        return name in self._declarations
    
    def add_reference(self, reference, name):
        definition = self.definition(name)
        self._references[reference] = definition
    
    def resolve(self, node):
        if node in self._references:
            return self._references[node]
        else:
            raise KeyError("Could not resolve {}".format(node))
    
    def enter_function(self, node):
        declarations = name_declaration.declarations_in_function(node)
        return self._enter(declarations)
    
    def enter_module(self, node):
        declarations = name_declaration.declarations_in_module(node)
        return self._enter(declarations)
    
    
    def _enter(self, new_declarations):
        declarations = self._declarations.copy()
        declarations.update(new_declarations)
        return Context(declarations, self._references)
