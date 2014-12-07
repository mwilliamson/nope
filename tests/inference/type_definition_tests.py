from nose.tools import istest, assert_equal

from nope import types, nodes
from .util import update_context


@istest
def type_definition_type_is_meta_type_of_type_value():
    type_bindings = {
        "str": types.meta_type(types.str_type),
        "int": types.meta_type(types.int_type),
    }
    node = nodes.type_definition("Identifier", nodes.type_union([nodes.ref("str"), nodes.ref("int")]))
    context = update_context(node, type_bindings=type_bindings)
    declared_type = context.lookup_name("Identifier")
    assert types.is_meta_type(declared_type)
    assert_equal(types.union(types.str_type, types.int_type), declared_type.type)

