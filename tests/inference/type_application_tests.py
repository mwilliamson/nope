from nose.tools import istest, assert_equal

from nope import types, nodes
from .util import infer


@istest
def type_of_type_application_is_metatype_of_applied_type():
    type_bindings = {
        "list": types.meta_type(types.list_type),
        "int": types.meta_type(types.int_type),
    }
    node = nodes.type_apply(nodes.ref("list"), [nodes.ref("int")])
    inferred_type = infer(node, type_bindings=type_bindings)
    assert types.is_meta_type(inferred_type)
    assert_equal(types.list_type(types.int_type), inferred_type.type)

