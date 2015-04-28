from nose.tools import istest, assert_equal

from nope import types, nodes
from .util import update_context


@istest
def type_of_structural_type_is_as_definition():
    type_bindings = {
        "str": types.meta_type(types.str_type),
        "int": types.meta_type(types.int_type),
    }
    node = nodes.structural_type("Song", [
        ("description", nodes.ref("str")),
        ("length", nodes.ref("int")),
    ])
    
    context = update_context(node, type_bindings=type_bindings)
    declared_type = context.lookup_name("Song")
    
    assert types.is_meta_type(declared_type)
    expected_type = types.structural_type("Song", [
        types.attr("description", types.str_type),
        types.attr("length", types.int_type),
    ])
    assert types.is_equivalent_type(expected_type, declared_type.type)

