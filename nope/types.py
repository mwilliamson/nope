import collections

ScalarType = collections.namedtuple("ScalarType", ["name", "attrs"])
GenericType = collections.namedtuple("GenericType", ["name"])
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
    if super_type == object:
        return True
    
    return super_type == sub_type


none_type = ScalarType("NoneType", {})

int = ScalarType("int", {})

str = ScalarType("str", {})
str.attrs["find"] = func([str], int)

type = TypeType

object = ScalarType("object", {})
