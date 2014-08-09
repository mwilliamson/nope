import collections

class ScalarType(collections.namedtuple("ScalarType", ["name", "attrs"])):
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return str(self)
    
    def substitute_types(self, param_map):
        return self

# TODO: number of type params
class _GenericType(collections.namedtuple("GenericType", ["name", "params", "attrs"])):
    def __call__(self, *args):
        return self.instantiate(list(args))
    
    def instantiate(self, params):
        param_map = dict(zip(self.params, params))
        instantiated_attrs = _substitute_types(self.attrs, param_map)
        return InstantiatedType(self, params, instantiated_attrs)

def generic_type(name, params, attrs):
    # We allow the caller to use string literals to represent formal params, so we need to replace them
    # e.g. generic_type("Foo", ["T"], {"x": "T"}) =>
    #           GenericType("Foo", [T], {"x": T}) where T = FormalParameter("T")
    formal_params = [_FormalParameter(param) for param in params]
    param_map = dict(zip(params, formal_params))
    return _GenericType(name, formal_params, _substitute_types(attrs, param_map))


def _substitute_types(type_, type_map):
    if isinstance(type_, dict):
        return dict(
            (name, _substitute_types(attr_type, type_map))
            for name, attr_type in type_.items()
        )
    if isinstance(type_, str):
        return type_map[type_]
    else:
        return type_.substitute_types(type_map)
        

class _FormalParameter(object):
    def __init__(self, name):
        self._name = name
    
    def substitute_types(self, type_map):
        return type_map.get(self, self)


class InstantiatedType(collections.namedtuple("InstantiatedType", ["generic_type", "params", "attrs"])):
    def substitute_types(self, type_map):
        # TODO: test shadowing
        
        instantiated_params = [
            _substitute_types(param_type, type_map)
            for param_type in self.params
        ]
        instantiated_attrs = _substitute_types(self.attrs, type_map)
        return InstantiatedType(self.generic_type, instantiated_params, instantiated_attrs)
        
    
TypeType = collections.namedtuple("TypeType", ["type"])
    

# TODO: set type params of func correctly (needs varargs?)
func_type = generic_type("func", [], {})

def func(args, return_type):
    return func_type.instantiate(list(args) + [return_type])



def is_sub_type(super_type, sub_type):
    if super_type == object_type:
        return True
    
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

list_type = generic_type("list", ["T"], {
    "__getitem__": func([int_type], "T"),
})

type_type = TypeType

object_type = ScalarType("object", {})

bottom_type = ScalarType("bottom", {})

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
