from nose.tools import istest, assert_equal

from nope import types, nodes

from .util import infer



@istest
def can_infer_type_of_none():
    assert_equal(types.none_type, infer(nodes.none()))


@istest
def can_infer_type_of_boolean_literal():
    assert_equal(types.bool_type, infer(nodes.bool_literal(True)))


@istest
def can_infer_type_of_int_literal():
    assert_equal(types.int_type, infer(nodes.int_literal("4")))


@istest
def can_infer_type_of_str_literal():
    assert_equal(types.str_type, infer(nodes.str_literal("!")))


@istest
def can_infer_type_of_list_of_two_tuple():
    assert_equal(
        types.tuple_type(types.int_type, types.str_type),
        infer(nodes.tuple_literal([nodes.int_literal(1), nodes.str_literal("42")]))
    )


@istest
def can_infer_type_of_list_of_ints():
    assert_equal(types.list_type(types.int_type), infer(nodes.list_literal([nodes.int_literal(1), nodes.int_literal(42)])))
    

@istest
def empty_list_has_elements_of_type_bottom():
    assert_equal(types.list_type(types.bottom_type), infer(nodes.list_literal([])))


@istest
def empty_list_can_be_typed_using_type_hint():
    assert_equal(
        types.list_type(types.int_type),
        infer(nodes.list_literal([]), hint=types.list_type(types.int_type))
    )


@istest
def empty_list_type_hint_is_ignored_if_type_hint_is_not_list():
    assert_equal(
        types.list_type(types.bottom_type),
        infer(nodes.list_literal([]), hint=types.int_type)
    )


@istest
def non_empty_list_can_be_typed_using_type_hint():
    assert_equal(
        types.list_type(types.object_type),
        infer(nodes.list_literal([nodes.int_literal(1)]), hint=types.list_type(types.object_type))
    )


@istest
def list_type_hint_is_ignored_if_not_super_type_of_elements():
    assert_equal(
        types.list_type(types.int_type),
        infer(nodes.list_literal([nodes.int_literal(1)]), hint=types.list_type(types.none_type))
    )


@istest
def type_of_dict_is_determined_by_unifying_types_of_keys_and_values():
    assert_equal(
        types.dict_type(types.str_type, types.int_type),
        infer(nodes.dict_literal([
            (nodes.str_literal("Hello"), nodes.int_literal(42)),
            (nodes.str_literal("Blah"), nodes.int_literal(16)),
        ]))
    )


@istest
def empty_dict_has_key_and_value_type_of_bottom():
    assert_equal(
        types.dict_type(types.bottom_type, types.bottom_type),
        infer(nodes.dict_literal([]))
    )


@istest
def dict_literal_uses_type_hint_when_valid():
    assert_equal(
        types.dict_type(types.object_type, types.int_type),
        infer(nodes.dict_literal([
            (nodes.str_literal("Hello"), nodes.int_literal(42)),
        ]), hint=types.dict_type(types.object_type, types.int_type))
    )
    assert_equal(
        types.dict_type(types.str_type, types.object_type),
        infer(nodes.dict_literal([
            (nodes.str_literal("Hello"), nodes.int_literal(42)),
        ]), hint=types.dict_type(types.str_type, types.object_type))
    )


@istest
def dict_literal_type_hint_is_ignored_if_hint_type_is_not_dict():
    assert_equal(
        types.dict_type(types.bottom_type, types.bottom_type),
        infer(nodes.dict_literal([]), hint=types.int_type)
    )


@istest
def dict_literal_type_hint_is_ignored_if_hint_item_type_is_not_super_type_of_actual_item_types():
    assert_equal(
        types.dict_type(types.str_type, types.int_type),
        infer(nodes.dict_literal([
            (nodes.str_literal("Hello"), nodes.int_literal(42)),
        ]), hint=types.dict_type(types.bottom_type, types.int_type))
    )
    assert_equal(
        types.dict_type(types.str_type, types.int_type),
        infer(nodes.dict_literal([
            (nodes.str_literal("Hello"), nodes.int_literal(42)),
        ]), hint=types.dict_type(types.str_type, types.bottom_type))
    )
