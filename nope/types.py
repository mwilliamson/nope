import collections

ScalarType = collections.namedtuple("ScalarType", ["name", "attrs"])

# TODO: number of type params
class GenericType(collections.namedtuple("GenericType", ["name"])):
    def __call__(self, *args):
        return InstantiatedType(self, list(args))

InstantiatedType = collections.namedtuple("InstantiatedType", ["generic_type", "params"])
TypeType = collections.namedtuple("TypeType", ["type"])

def func(args, return_type):
    return generic_type("func")(list(args) + [return_type])

def generic_type(name):
    generic_type = GenericType(name)
    def instantiate(params):
        return InstantiatedType(generic_type, params)
    
    return instantiate


def is_sub_type(super_type, sub_type):
    if super_type == object_type:
        return True
    
    return super_type == sub_type


none_type = ScalarType("NoneType", {})

boolean_type = ScalarType("BooleanType", {})

int_type = ScalarType("int", {})

str_type = ScalarType("str", {})
str_type.attrs["find"] = func([str_type], int_type)

list_type = GenericType("list")

type_type = TypeType

object_type = ScalarType("object", {})


def unify(types):
    for type_ in types:
        if not is_sub_type(types[0], type_):
            return object_type
    
    return types[0]


class Module(object):
    def __init__(self, name, attrs):
        self.name = name
        self.attrs = attrs
