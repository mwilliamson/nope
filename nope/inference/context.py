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
        self._update_declaration_type(node, declaration, type_)
    
    def _update_declaration_type(self, node, declaration, type_):
        existing_type = self._declaration_types.get(declaration)
        if existing_type is None:
            self._declaration_types[declaration] = type_
        elif not types.is_sub_type(existing_type, type_):
            raise errors.UnexpectedTargetTypeError(node, value_type=type_, target_type=existing_type)
    
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
    
    def instantiate_types(self, types):
        override_declaration_types = dict(
            (self.referenced_declaration(node), type_)
            for node, type_ in types
        )
        return Context(
            self._references,
            _OverrideDict(self._declaration_types, dict(override_declaration_types)),
            self._deferred,
            return_type=self.return_type,
            is_module_scope=self.is_module_scope,
        )
    
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


class _OverrideDict(object):
    def __init__(self, values, overrides):
        self._values = values
        self._overrides = overrides.copy()
    
    def __contains__(self, key):
        return key in self._values or key in self._overrides
    
    def get(self, key):
        return self._overrides.get(key, self._values.get(key))
    
    def __getitem__(self, key):
        if key in self._overrides:
            return self._overrides[key]
        return self._values[key]
    
