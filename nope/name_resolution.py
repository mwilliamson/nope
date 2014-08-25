from nope import nodes, errors, name_declaration, visit


def resolve(node, context):
    visitor = visit.Visitor()
    visitor.replace(nodes.VariableReference, _resolve_variable_reference)
    visitor.replace(nodes.FunctionDef, _resolve_function_def)
    visitor.replace(nodes.Import, _resolve_import)
    visitor.replace(nodes.ImportFrom, _resolve_import)
    
    return visitor.visit(node, context)


def _resolve_variable_reference(visitor, node, context):
    if not context.is_defined(node.name):
        raise errors.UndefinedNameError(node, node.name)
    
    context.add_reference(node, node.name)


def _resolve_function_def(visitor, node, context):
    context.add_reference(node, node.name)
    
    body_context = context.enter_function(node)
    for arg in node.args.args:
        body_context.add_reference(arg, arg.name)
    
    for statement in node.body:
        visitor.visit(statement, body_context)


def _resolve_import(visitor, node, context):
    for alias in node.names:
        context.add_reference(alias, alias.value_name)
    

class Context(object):
    def __init__(self, definitions, references):
        self._definitions = definitions
        self._references = references
    
    def define(self, name):
        if name not in self._definitions:
            self._definitions[name] = NameDefinition(name)
    
    def definition(self, name):
        return self._definitions[name]

    def is_defined(self, name):
        return name in self._definitions
    
    def add_reference(self, reference, name):
        definition = self.definition(name)
        self._references[id(reference)] = definition
    
    def resolve(self, node):
        return self._references[id(node)]
    
    def enter_function(self, node):
        definitions = self._definitions.copy()
        
        declared_names = name_declaration.declarations_in_function(node).keys()
            
        for name in declared_names:
            definitions[name] = NameDefinition(name)
        
        return Context(definitions, self._references)


class NameDefinition(object):
    def __init__(self, name):
        self.name = name
