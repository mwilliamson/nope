from nose.tools import istest, assert_equal

from nope import types, nodes
from .util import infer


@istest
def can_infer_type_of_list_comprehension_over_list():
    type_bindings = {"xs": types.list_type(types.str_type)}
    node = nodes.list_comprehension(
        nodes.int_literal(1),
        nodes.ref("x"),
        nodes.ref("xs"),
    )
    assert_equal(
        types.list_type(types.int_type),
        infer(node, type_bindings=type_bindings)
    )


@istest
def can_infer_type_of_generator_expression_over_list():
    type_bindings = {"xs": types.list_type(types.str_type)}
    node = nodes.generator_expression(
        nodes.int_literal(1),
        nodes.ref("x"),
        nodes.ref("xs"),
    )
    assert_equal(
        types.iterator(types.int_type),
        infer(node, type_bindings=type_bindings)
    )


@istest
def target_of_comprehension_is_available_in_element():
    type_bindings = {"xs": types.list_type(types.str_type)}
    node = nodes.list_comprehension(
        nodes.ref("x"),
        nodes.ref("x"),
        nodes.ref("xs"),
    )
    assert_equal(
        types.list_type(types.str_type),
        infer(node, type_bindings=type_bindings)
    )
