from nose.tools import istest, assert_equal

from nope import types, nodes
from .util import infer


@istest
def type_of_function_signature_is_metatype_of_function():
    type_bindings = {
        "str": types.meta_type(types.str_type),
        "int": types.meta_type(types.int_type),
    }
    node = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("str")
    )
    inferred_type = infer(node, type_bindings=type_bindings)
    assert types.is_meta_type(inferred_type)
    assert_equal(types.func([types.int_type], types.str_type), inferred_type.type)


@istest
def type_of_function_signature_is_metatype_of_function():
    node = nodes.signature(
        type_params=[nodes.formal_type_parameter("T")],
        args=[nodes.signature_arg(nodes.ref("T"))],
        returns=nodes.ref("T")
    )
    inferred_type = infer(node)
    assert types.is_meta_type(inferred_type)
    assert types.is_generic_func(inferred_type.type)
    formal_type_param, = inferred_type.type.formal_type_params
    assert_equal(
        types.func([formal_type_param], formal_type_param),
        inferred_type.type.instantiate([formal_type_param]),
    )
