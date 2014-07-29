from . import types


class Context(object):
    def __init__(self, bindings, return_type=None):
        self._vars = bindings
        self.return_type = return_type
    
    def add(self, name, binding):
        # TODO: prohibit overrides
        self._vars[name] = binding
    
    def lookup(self, name):
        return self._vars[name]
    
    def enter_func(self, return_type, local_names):
        func_vars = self._vars.copy()
        for local_name in local_names:
            func_vars[local_name] = None
        return Context(func_vars, return_type=return_type)
    
    def enter_module(self):
        return Context(self._vars.copy(), return_type=None)


module_context = Context({
    "int": types.type(types.int),
    "str": types.type(types.str),
    "none": types.type(types.none_type),
    "print": types.func([types.object], types.none_type),
})

def new_module_context():
    return module_context.enter_module()
