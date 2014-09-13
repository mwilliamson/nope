from nose.tools import istest, assert_equal

from nope import types, nodes

from .util import infer



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


@istest
def type_of_dict_is_determined_by_unifying_types_of_keys_and_values():
    assert_equal(
        types.dict_type(types.str_type, types.int_type),
        infer(nodes.dict_literal([
            (nodes.string("Hello"), nodes.int(42)),
            (nodes.string("Blah"), nodes.int(16)),
        ]))
    )
