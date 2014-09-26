from nose.tools import istest, assert_equal, assert_is

from nope import types, nodes, errors
from nope.inference import ephemeral
from .util import assert_type_mismatch, infer


@istest
def type_of_type_application_is_metatype_of_applied_type():
    type_bindings = {
        "list": types.meta_type(types.list_type),
        "int": types.meta_type(types.int_type),
    }
    node = nodes.type_apply(nodes.ref("list"), [nodes.ref("int")])
    assert_equal(
        types.list_type(types.int_type),
        infer(node, type_bindings=type_bindings)
    )

