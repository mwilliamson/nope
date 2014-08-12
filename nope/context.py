import collections

from . import types, errors


Variable = collections.namedtuple("Variable", ["var_type", "is_bound"])
Variable.unbound = lambda: Variable(None, is_bound=False)

def _create_vars(bindings):
    return dict(
        (name, _create_var(binding))
        for name, binding in bindings.items()
    )


def _create_var(binding):
    if isinstance(binding, Variable):
        return binding
    else:
        return Variable(binding, is_bound=binding is not None)



def bound_context(bindings):
    return _Context(_create_vars(bindings))


class _Context(object):
    def __init__(self, bindings, return_type=None, is_module_scope=False, in_loop=False):
        self._vars = bindings
        self.return_type = return_type
        self.is_module_scope = is_module_scope
        self.in_loop = in_loop
    
    def has_name(self, name):
        return name in self._vars
    
    def is_bound(self, name):
        return self._vars[name].is_bound
    
    def add(self, node, name, var_type):
        # All names should be declared on entering a scope, so if `name` isn't
        # in `self._vars` it's a programming error i.e. a bug in the type checker
        variable = self._vars[name]
        if variable.is_bound:
            # TODO: raise a proper TypeCheckError with a node attribute, or push responsibility into inference.py
            raise Exception("Variable is already bound")
        else:
            self._vars[name] = Variable(var_type, is_bound=True)
    
    def lookup(self, name, allow_unbound=False):
        variable = self._vars[name]
        if allow_unbound or variable.is_bound:
            return self._vars[name].var_type
        else:
            raise Exception("Variable is not bound: '{}'".format(name))
    
    def enter_func(self, return_type, local_names):
        func_vars = self._vars.copy()
        for local_name in local_names:
            func_vars[local_name] = Variable.unbound()
        return _Context(func_vars, return_type=return_type, is_module_scope=False)
    
    def enter_module(self, declared_names):
        module_vars = self._vars.copy()
        for name in declared_names:
            module_vars[name] = Variable.unbound()
        return _Context(module_vars, return_type=None, is_module_scope=True)
    
    def enter_loop(self):
        return self._enter_block(in_loop=True)
    
    def enter_if_else_branch(self):
        return self._enter_block(in_loop=self.in_loop)

    
    def unify(self, contexts, bind):
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
            if not self.is_bound(key):
                variables = [bindings.get(key, Variable.unbound()) for bindings in new_bindings]
                var_types = [
                    variable.var_type
                    for variable in variables
                    if variable.var_type is not None
                ]
                if len(var_types) > 0:
                    unified_type = types.unify(var_types)
                    is_bound = bind and all(variable.is_bound for variable in variables)
                    self._vars[key] = Variable(unified_type, is_bound)

    def _enter_block(self, in_loop=False):
        return _Context(
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


module_context = bound_context({
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
