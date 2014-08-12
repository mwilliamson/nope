from . import types, errors


class Context(object):
    def __init__(self, bindings, return_type=None, is_module_scope=False, in_loop=False):
        self._vars = bindings
        self.return_type = return_type
        self.is_module_scope = is_module_scope
        self.in_loop = in_loop
    
    def has_name(self, name):
        return name in self._vars
    
    def add(self, node, name, binding):
        # All names should be declared on entering a scope, so if `name` isn't
        # in `self._vars` it's a programming error i.e. a bug in the type checker
        var_type = self._vars[name]
        if var_type is None or types.is_sub_type(var_type, binding):
            self._vars[name] = binding
        else:
            raise errors.TypeMismatchError(node, expected=var_type, actual=binding)
    
    def lookup(self, name):
        return self._vars[name]
    
    def enter_func(self, return_type, local_names):
        func_vars = self._vars.copy()
        for local_name in local_names:
            func_vars[local_name] = None
        return Context(func_vars, return_type=return_type, is_module_scope=False)
    
    def enter_module(self, declared_names):
        module_vars = self._vars.copy()
        for name in declared_names:
            module_vars[name] = None
        return Context(module_vars, return_type=None, is_module_scope=True)
    
    def enter_loop(self):
        return self._enter_block(in_loop=True)
    
    def enter_if_else_branch(self):
        return self._enter_block(in_loop=self.in_loop)

    
    def unify(self, contexts):
        new_bindings = [
            context._vars._new_vars
            for context in contexts
        ]
        new_keys = set(
            key
            for bindings in new_bindings
            for key in bindings
        )
        
        for key in new_keys:
            var_types = [bindings.get(key) for bindings in new_bindings]
            if not any(var_type is None for var_type in var_types):
                unified_type = types.unify(var_types)
                self.add(None, key, unified_type)

    def _enter_block(self, in_loop=False):
        return Context(
            BlockVars(self._vars),
            return_type=self.return_type,
            is_module_scope=self.is_module_scope,
            in_loop=in_loop,
        )


class BlockVars(object):
    def __init__(self, bindings):
        self._original_vars = bindings
        self._new_vars = {}
    
    def __getitem__(self, key):
        if key in self._new_vars:
            return self._new_vars[key]
        else:
            return self._original_vars[key]
    
    def __setitem__(self, key, value):
        self._new_vars[key] = value
    
    def __contains__(self, key):
        return key in self._original_vars


module_context = Context({
    "object": types.type_type(types.object_type),
    "int": types.type_type(types.int_type),
    "str": types.type_type(types.str_type),
    "none": types.type_type(types.none_type),
    
    "print": types.func([types.object_type], types.none_type),
    "bool": types.func([types.object_type], types.boolean_type),
    # TODO: make abs generic e.g. T => T -> T
    "abs": types.func([types.int_type], types.int_type),
    "range": types.func([types.int_type, types.int_type], types.iterable(types.int_type)),
})

def new_module_context(declared_names):
    return module_context.enter_module(declared_names)
