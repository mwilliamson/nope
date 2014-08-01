from . import types, errors


class Context(object):
    def __init__(self, bindings, return_type=None, is_module_scope=False):
        self._vars = bindings
        self.return_type = return_type
        self.is_module_scope = is_module_scope
    
    def add(self, node, name, binding):
        # TODO: raise error if name not in self._vars
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


module_context = Context({
    "int": types.type_type(types.int_type),
    "str": types.type_type(types.str_type),
    "none": types.type_type(types.none_type),
    "print": types.func([types.object_type], types.none_type),
})

def new_module_context(declared_names):
    return module_context.enter_module(declared_names)
