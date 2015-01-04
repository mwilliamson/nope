from .. import errors, types


class Context(object):
    def __init__(self, references, declaration_types, deferred, return_type=None, is_module_scope=False):
        if isinstance(declaration_types, dict):
            declaration_types = DiffDict(declaration_types)
        
        self._references = references
        self._declaration_types = declaration_types
        self.return_type = return_type
        self.is_module_scope = is_module_scope
        self._deferred = deferred
    
    def update_type(self, node, type_):
        declaration = self._references.referenced_declaration(node)
        self.update_declaration_type(declaration, type_)
    
    def update_declaration_type(self, declaration, type_):
        self._declaration_types[declaration] = type_
        
    
    def lookup(self, node, allow_unbound=False):
        declaration = self._references.referenced_declaration(node)
        
        if declaration in self._declaration_types or allow_unbound:
            return self._declaration_types.get(declaration)
        else:
            raise errors.UnboundLocalError(node, node.name)
    
    def lookup_declaration(self, declaration):
        return self._declaration_types[declaration]
    
    def referenced_declaration(self, node):
        return self._references.referenced_declaration(node)
    
    def enter_func(self, return_type):
        return Context(
            self._references,
            self._declaration_types,
            self._deferred,
            return_type=return_type,
            is_module_scope=False,
        )
    
    def enter_class(self):
        return Context(
            self._references,
            self._declaration_types,
            self._deferred,
            return_type=None,
            is_module_scope=False,
        )
    
    def enter_module(self):
        return Context(
            self._references,
            self._declaration_types,
            self._deferred,
            return_type=None,
            is_module_scope=True,
        )
    
    def enter_statement(self):
        return Context(
            self._references,
            DiffDict(self._declaration_types),
            self._deferred,
            return_type=self.return_type,
            is_module_scope=self.is_module_scope,
        )
    
    def update_declaration_types(self, other_contexts):
        updated_declarations = set(
            key
            for other_context in other_contexts
            for key in other_context._declaration_types.updated_keys()
        )
        for declaration in updated_declarations:
            # TODO: set type to nothing if declaration is not in one of the contexts
            # (which possibly makes the name_binding module redundant)
            self._declaration_types[declaration] = types.common_super_type([
                context.lookup_declaration(declaration)
                for context in other_contexts
                if declaration in context._declaration_types
            ])
    
    def add_deferred(self, node, type_check):
        if node not in self._deferred:
            self._deferred[node] = []
            
        self._deferred[node].append(type_check)
    
    def update_deferred(self, node=None):
        if node is None:
            while self._deferred:
                for update in self._deferred.popitem()[1]:
                    update()
                
        elif node in self._deferred:
            for update in self._deferred.pop(node):
                update()


class DiffDict(object):
    def __init__(self, original):
        self._original = original
        self._updates = {}
    
    def __contains__(self, key):
        return key in self._original or key in self._updates
    
    def get(self, key):
        return self._updates.get(key, self._original.get(key))
    
    def __getitem__(self, key):
        if key in self._updates:
            return self._updates[key]
        return self._original[key]
    
    def __setitem__(self, key, value):
        self._updates[key] = value
    
    def updated_keys(self):
        return self._updates.keys()
