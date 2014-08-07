import collections

class ScalarType(collections.namedtuple("ScalarType", ["name", "attrs"])):
    def __str__(self):
        return self.name

# TODO: number of type params
class GenericType(collections.namedtuple("GenericType", ["name"])):
    def __call__(self, *args):
        return self.instantiate(list(args))
    
    def instantiate(self, params):
        return InstantiatedType(self, params)

generic_type = GenericType

InstantiatedType = collections.namedtuple("InstantiatedType", ["generic_type", "params"])
TypeType = collections.namedtuple("TypeType", ["type"])

func_type = generic_type("func")

def func(args, return_type):
    return func_type.instantiate(list(args) + [return_type])



def is_sub_type(super_type, sub_type):
    if super_type == object_type:
        return True
    
    return super_type == sub_type


none_type = ScalarType("NoneType", {})

boolean_type = ScalarType("BooleanType", {})

int_type = ScalarType("int", {})
int_type.attrs["__add__"] = func([int_type], int_type)
int_type.attrs["__sub__"] = func([int_type], int_type)
int_type.attrs["__mul__"] = func([int_type], int_type)
int_type.attrs["__truediv__"] = func([int_type], int_type)
int_type.attrs["__floordiv__"] = func([int_type], int_type)

str_type = ScalarType("str", {})
str_type.attrs["find"] = func([str_type], int_type)

list_type = GenericType("list")

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
