from . import errors


class Context(object):
    def __init__(self, references, definition_types, return_type=None, is_module_scope=False, is_class=False, class_type=None):
        self._references = references
        self._definition_types = definition_types
        self.return_type = return_type
        self.is_module_scope = is_module_scope
        self.is_class = is_class
        self.class_type = class_type
    
    def update_type(self, node, type_):
        declaration = self._references.referenced_declaration(node)
        self.update_declaration_type(declaration, type_)
    
    def update_declaration_type(self, declaration, type_):
        if declaration in self._definition_types:
            # TODO: raise a proper TypeCheckError with a node attribute, or push responsibility into inference.py
            raise Exception("definition already has a type")
        else:
            self._definition_types[declaration] = type_
        
    
    def lookup(self, node, allow_unbound=False):
        definition = self._references.referenced_declaration(node)
        if definition in self._definition_types or allow_unbound:
            return self._definition_types.get(definition)
        else:
            raise errors.UnboundLocalError(node, node.name)
    
    def lookup_declaration(self, declaration):
        return self._definition_types[declaration]
    
    def referenced_declaration(self, node):
        return self._references.referenced_declaration(node)
    
    def enter_func(self, return_type):
        return Context(
            self._references,
            self._definition_types,
            return_type=return_type,
            is_module_scope=False,
            is_class=False,
        )
    
    def enter_class(self, class_type):
        return Context(
            self._references,
            self._definition_types,
            return_type=None,
            is_module_scope=False,
            is_class=True,
            class_type=class_type,
        )
    
    def enter_module(self):
        return Context(
            self._references,
            self._definition_types,
            return_type=None,
            is_module_scope=True,
            is_class=False,
        )
