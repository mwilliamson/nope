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
    def __init__(self, params, create_type, complete_type):
        self.params = params
        self._create_type = create_type
        self._complete_type = complete_type
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
            new_type = self._create_type(*params)
            self._generic_cache[params] = _InstantiatedType(
                self,
                params,
                new_type,
                lambda: self._complete_type(new_type, *params),
            )
        
        return self._generic_cache[params]
    
    def is_instantiated_type(self, other):
        return (
            isinstance(other, _InstantiatedType) and
            other.generic_type == self
        )


def is_generic_type(type_):
    return isinstance(type_, _GenericType)


class _InstantiatedType(object):
    def __init__(self, generic_type, type_params, underlying_type, complete_type):
        self.generic_type = generic_type
        self.type_params = type_params
        self._underlying_type = underlying_type
        self._is_complete = False
        self._complete_type = complete_type
    
    def _ensure_complete(self):
        if not self._is_complete:
            self._complete_type()
    
    @property
    def name(self):
        return self._underlying_type.name
    
    @property
    def attrs(self):
        self._ensure_complete()
        return self._underlying_type.attrs
    
    def reify(self):
        self._ensure_complete()
        return self._underlying_type
        
    def __str__(self):
        return str(self._underlying_type)


def is_instantiated_type(type_):
    return isinstance(type_, _InstantiatedType)


def generic(params, create_type, attrs=None, complete_type=None):
    if complete_type is None:
        def complete_type(new_type, *params):
            if attrs is not None:
                new_type.attrs = attrs_from_iterable(attrs(*params))
    
    formal_params = [_formal_param(param) for param in params]
    return _GenericType(formal_params, create_type, complete_type)


class _GenericFunc(object):
    def __init__(self, formal_type_params, create_func):
        self.formal_type_params = formal_type_params
        self._create_func = create_func
        self._generic_signature = create_func(*formal_type_params)
        self.attrs = EmptyAttributes()
    
    @property
    def args(self):
        return self._generic_signature.args
    
    @property
    def return_type(self):
        return self._generic_signature.return_type
    
    def instantiate(self, params):
        return self._create_func(*params)
    
    def instantiate_with_type_map(self, type_map):
        params = [
            type_map[formal_type_param]
            for formal_type_param in self.formal_type_params
        ]
        return self.instantiate(params)
    
    def __str__(self):
        return "{} => {}".format(", ".join(map(str, self.formal_type_params)), self._generic_signature)
    

def generic_func(formal_type_params, create_func):
    formal_type_params = [_formal_param(param) for param in formal_type_params]
    return _GenericFunc(formal_type_params, create_func)


def is_generic_func(value):
    return isinstance(value, _GenericFunc)


def generic_class(name, formal_params, attrs=None):
    if attrs is None:
        attrs = lambda *params: []
    
    return generic(
        formal_params,
        lambda *params: class_type(_instantiated_type_name(name, params)),
        attrs=attrs,
    )

def _instantiated_type_name(name, params):
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
        formal_params,
        lambda *params: structural_type(_instantiated_type_name(name, params)),
        attrs=attrs,
    )
