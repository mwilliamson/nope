from nose.tools import istest, assert_equal

from nope import types, nodes
from nope.inference import infer as _infer
from nope.context import Context


def infer(node):
    return _infer(node, Context({}))


@istest
def can_infer_type_of_none():
    assert_equal(types.none_type, infer(nodes.none()))


@istest
def can_infer_type_of_boolean_literal():
    assert_equal(types.boolean_type, infer(nodes.boolean(True)))


@istest
def can_infer_type_of_int_literal():
    assert_equal(types.int_type, infer(nodes.int("4")))


@istest
def can_infer_type_of_str_literal():
    assert_equal(types.str_type, infer(nodes.string("!")))


@istest
def can_infer_type_of_list_of_ints():
    assert_equal(types.list_type(types.int_type), infer(nodes.list([nodes.int(1), nodes.int(42)])))
    

@istest
def empty_list_has_elements_of_type_bottom():
    assert_equal(types.list_type(types.bottom_type), infer(nodes.list([])))