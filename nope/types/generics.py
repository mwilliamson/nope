from .attributes import EmptyAttributes, attrs_from_iterable
from .classes import class_type
from .structural import structural_type


class _GenericTypeAttributes(object):
    def __init__(self, params, attrs):
        self._params = params
        self._attrs = attrs
    
    def add(self, name, type_, read_only=True):
        self._attrs.add(name, type_(*self._params), read_only=read_only)


class _GenericType(object):
    def __init__(self, params, inner_type):
        self.params = params
        self._inner_type = inner_type
        # TODO: the cache lives too long -- for instance,
        # builtin types such as int will never evict anything from the cache,
        # and will never be deleted, meaning it will grow on each compilation
        self._generic_cache = {}
    
    def __call__(self, *args):
        return self.instantiate(args)
    
    def instantiate(self, params):
        if len(params) != len(self.params):
            raise Exception("generic type requires exactly {} type parameter(s)".format(len(self.params)))
        
        params = tuple(params)
        
        if params not in self._generic_cache:
            new_type = self._inner_type.replace_types()
            new_type.name = _instantiated_type_name(self._name, params)
            self._generic_cache[params] = self._inner_type.replace_types()
        
        return self._generic_cache[params]


def is_generic_type(type_):
    return isinstance(type_, _GenericType)


def generic(params, inner_type):
    formal_params = [_formal_param(param) for param in params]
    return _GenericType(formal_params, inner_type)


def unnamed_generic(params, create_type, attrs=None, complete_type=None):
    return generic(
        name=None,
        params=params,
        create_type=lambda name, *actual_params: create_type(*actual_params),
        attrs=attrs,
        complete_type=complete_type,
    )


class _GenericFunc(object):
    def __init__(self, formal_type_params, inner_func):
        self.formal_type_params = formal_type_params
        self._inner_func = inner_func
        self.attrs = EmptyAttributes()
    
    @property
    def args(self):
        return self._inner_func.args
    
    @property
    def return_type(self):
        return self._inner_func.return_type
    
    def instantiate(self, params):
        return self.instantiate_with_type_map(dict(zip(self.formal_type_params, params)))
    
    def instantiate_with_type_map(self, type_map):
        return self._inner_func.replace_types(type_map)
    
    def __str__(self):
        return "{} => {}".format(", ".join(map(str, self.formal_type_params)), self._inner_func)
    

def generic_func(formal_type_params, inner_func):
    return _GenericFunc(formal_type_params, inner_func)


def generic_func_builder(formal_type_param_names, create_inner_func):
    formal_type_params = [_formal_param(param) for param in formal_type_param_names]
    return generic_func(formal_type_params, create_inner_func(*formal_type_params))


def is_generic_func(value):
    return isinstance(value, _GenericFunc)


def generic_class(name, formal_params, attrs=None):
    if attrs is None:
        attrs = lambda *params: []
    
    return generic(
        name,
        formal_params,
        lambda name, *params: class_type(name),
        attrs=attrs,
    )

def _instantiated_type_name(name, params):
    if name is None:
        return None
    else:
        return "{}[{}]".format(name, ", ".join(map(str, params)))


class Variance(object):
    Invariant, Covariant, Contravariant = range(3)


class _FormalParameter(object):
    def __init__(self, name, variance):
        self._name = name
        self.variance = variance
    
    def __str__(self):
        return self._name
    
    def __repr__(self):
        return "_FormalParameter({}, {})".format(self._name, self.variance)
    
    def replace_types(self, type_map):
        return type_map.get(self, self)


def is_formal_parameter(nope_type):
    return isinstance(nope_type, _FormalParameter)


def _formal_param(param):
    if isinstance(param, _FormalParameter):
        return param
    else:
        return _FormalParameter(param, Variance.Invariant)


def invariant(name):
    return _FormalParameter(name, Variance.Invariant)


def covariant(name):
    return _FormalParameter(name, Variance.Covariant)


def contravariant(name):
    return _FormalParameter(name, Variance.Contravariant)


def generic_structural_type(name, formal_params, attrs=None):
    return generic(
        name,
        formal_params,
        lambda name, *params: structural_type(name),
        attrs=attrs,
    )
