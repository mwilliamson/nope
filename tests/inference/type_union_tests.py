from nose.tools import istest, assert_equal

from nope import types, nodes
from .util import infer


@istest
def type_of_type_union_is_metatype_of_unioned_types():
    type_bindings = {
        "str": types.meta_type(types.str_type),
        "int": types.meta_type(types.int_type),
    }
    node = nodes.type_union([nodes.ref("str"), nodes.ref("int")])
    inferred_type = infer(node, type_bindings=type_bindings)
    assert types.is_meta_type(inferred_type)
    assert_equal(types.union(types.str_type, types.int_type), inferred_type.type)

