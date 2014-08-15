import collections


class GenericTypeAttributes(object):
    def __init__(self, params, attrs):
        self._params = params
        self._attrs = attrs
    
    def __setitem__(self, name, create_attr):
        self._attrs[name] = create_attr(*self._params)


class ScalarType(object):
    def __init__(self, name, attrs, base_classes=None):
        if base_classes is None:
            base_classes = []
        
        self.name = name
        self.attrs = attrs
        self.base_classes = base_classes
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return str(self)
    
    def substitute_types(self, type_map):
        return self


# TODO: number of type params
class _GenericType(object):
    def __init__(self, params, underlying_type):
        self.underlying_type = underlying_type
        self.params = params
        self.attrs = GenericTypeAttributes(params, underlying_type.attrs)
    
    def __call__(self, *args):
        return self.instantiate(list(args))
    
    def instantiate(self, params):
        param_map = dict(zip(self.params, params))
        instantiated_attrs = _substitute_types(self.underlying_type.attrs, param_map)
        return InstantiatedType(self, params, instantiated_attrs)
    
    def is_instantiated_type(self, other):
        # TODO: handle subtyping
        return isinstance(other, InstantiatedType) and other.generic_type == self
    
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return str(self)


def _generic_type(params, underlying_type, attrs=None):
    if attrs is None:
        attrs = {}
    
    formal_params = [_FormalParameter(param) for param in params]
    param_map = dict(zip(params, formal_params))
    generic_class = _GenericType(formal_params, underlying_type)
    
    for name, create_attr in attrs.items():
        generic_class.attrs[name] = create_attr
    
    return generic_class


def generic_class(name, params, attrs=None):
    return _generic_type(params, ScalarType(name, {}), attrs)


def _substitute_types(type_, type_map):
    if isinstance(type_, dict):
        return dict(
            (name, _substitute_types(attr_type, type_map))
            for name, attr_type in type_.items()
        )
    else:
        return type_.substitute_types(type_map)


class _FormalParameter(object):
    def __init__(self, name):
        self._name = name
    
    def substitute_types(self, type_map):
        return type_map.get(self, self)


class InstantiatedType(object):
    def __init__(self, generic_type, params, attrs):
        self.generic_type = generic_type
        self.params = params
        self.attrs = attrs
    
    def substitute_types(self, type_map):
        # TODO: test shadowing
        
        instantiated_params = [
            _substitute_types(param_type, type_map)
            for param_type in self.params
        ]
        instantiated_attrs = _substitute_types(self.attrs, type_map)
        return InstantiatedType(self.generic_type, instantiated_params, instantiated_attrs)
    
    def __eq__(self, other):
        if not isinstance(other, InstantiatedType):
            return False
            
        return self.generic_type == other.generic_type and self.params == other.params
    
    def __neq__(self, other):
        return not (self == other)
    
    def __str__(self):
        return "{}[{}]".format(self.generic_type, ", ".join(map(str, self.params)))
    
    def __repr__(self):
        return str(self)


class StructuralType(object):
    def __init__(self, name, attrs):
        self.name = name
        self.attrs = attrs


structural_type = StructuralType

def generic_structural_type(name, params, attrs=None):
    return _generic_type(params, structural_type(name, {}), attrs)

    
TypeType = collections.namedtuple("TypeType", ["type", "attrs"])
    

# TODO: set type params of func correctly (needs varargs?)
func_type = generic_class("func", [])

def func(args, return_type):
    return func_type.instantiate(list(args) + [return_type])



def is_sub_type(super_type, sub_type):
    if super_type == object_type:
        return True
    
    if isinstance(sub_type, ScalarType) and super_type in sub_type.base_classes:
        return True
    
    if isinstance(super_type, StructuralType):
        return all(
            is_sub_type(super_type.attrs[name], sub_type.attrs.get(name))
            for name, attr in super_type.attrs.items()
        )
    
    return super_type == sub_type


none_type = ScalarType("NoneType", {})

boolean_type = ScalarType("BooleanType", {})

int_type = ScalarType("int", {})

float_type = ScalarType("float", {})

int_type.attrs["__add__"] = func([int_type], int_type)
int_type.attrs["__sub__"] = func([int_type], int_type)
int_type.attrs["__mul__"] = func([int_type], int_type)
int_type.attrs["__truediv__"] = func([int_type], float_type)
int_type.attrs["__floordiv__"] = func([int_type], int_type)
int_type.attrs["__mod__"] = func([int_type], int_type)

int_type.attrs["__neg__"] = func([], int_type)
int_type.attrs["__pos__"] = func([], int_type)
int_type.attrs["__abs__"] = func([], int_type)
int_type.attrs["__invert__"] = func([], int_type)

str_type = ScalarType("str", {})
str_type.attrs["find"] = func([str_type], int_type)

# TODO: should be a structural type (with __next__)
iterator = generic_structural_type("iterator", ["T"])
iterator.attrs["__iter__"] = lambda T: func([], iterator(T))
iterator.attrs["__next__"] = lambda T: func([], T)

iterable = generic_structural_type("iterable", ["T"])
iterable.attrs["__iter__"] = lambda T: func([], iterator(T))

list_type = generic_class("list", ["T"], {
    "__getitem__": lambda T: func([int_type], T),
    "__setitem__": lambda T: func([int_type, T], none_type),
    "__iter__": lambda T: func([], iterator(T)),
    "append": lambda T: func([T], none_type),
})

def type_type(name, attrs=None):
    if attrs is None:
        attrs = {}
    
    return TypeType(name, attrs)

any_type = object_type = ScalarType("object", {})

bottom_type = ScalarType("bottom", {})

exception_type = ScalarType("Exception", {})
exception_meta_type = type_type(exception_type, {
    "__call__": func([str_type], exception_type)
})

def unify(types):
    if len(types) == 0:
        return bottom_type
        
    for type_ in types:
        if not is_sub_type(types[0], type_):
            return object_type
    
    return types[0]


class Module(object):
    def __init__(self, name, attrs):
        self.name = name
        self.attrs = attrs


class TypeLookup(object):
    def __init__(self, types):
        self._types = types
    
    def type_of(self, node):
        return self._types.get(id(node))
