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
    if super_type == object:
        return True
    
    return super_type == sub_type


none_type = ScalarType("NoneType", {})

int = ScalarType("int", {})

str = ScalarType("str", {})
str.attrs["find"] = func([str], int)

list_type = GenericType("list")

type = TypeType

object = ScalarType("object", {})


def unify(types):
    for type_ in types:
        if not is_sub_type(types[0], type_):
            # TODO: raise more appropriate exception
            raise Exception("Could not unify types")
    
    return types[0]
