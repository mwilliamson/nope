from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import ephemeral

from .util import infer, assert_subexpression_is_type_checked


@istest
def can_infer_type_of_addition_operation():
    type_bindings = {"x": types.int_type, "y": types.int_type}
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(addition, type_bindings=type_bindings))


@istest
def cannot_add_int_and_str():
    type_bindings = {"x": types.int_type, "y": types.str_type}
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(addition.right, error.node)
        assert_equal(types.int_type, error.expected)
        assert_equal(types.str_type, error.actual)


@istest
def operands_of_add_operation_must_support_add():
    type_bindings = {"x": types.none_type, "y": types.none_type}
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.NoSuchAttributeError as error:
        assert_equal(nodes.attr(addition.left, "__add__"), error.node)
        assert_equal(addition.left, ephemeral.root_node(error.node))


@istest
def right_hand_operand_must_be_sub_type_of_formal_argument():
    type_bindings = {"x": types.int_type, "y": types.object_type}
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(addition.right, error.node)
        assert_equal(types.int_type, error.expected)
        assert_equal(types.object_type, error.actual)


@istest
def type_of_add_method_argument_allows_super_type():
    cls = types.class_type("Addable", {})
    cls.attrs.add("__add__", types.func([types.object_type], cls))
    
    type_bindings = {"x": cls, "y": cls}
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(cls, infer(addition, type_bindings=type_bindings))


@istest
def add_method_should_only_accept_one_argument():
    cls = types.class_type("NotAddable", {})
    cls.attrs.add("__add__", types.func([types.object_type, types.object_type], cls))
    
    type_bindings = {"x": cls, "y": cls}
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(addition, ephemeral.root_node(error.node))


@istest
def return_type_of_add_can_differ_from_original_type():
    cls = types.class_type("Addable", {})
    cls.attrs.add("__add__", types.func([types.object_type], types.object_type))
    
    type_bindings = {"x": cls, "y": cls}
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.object_type, infer(addition, type_bindings=type_bindings))


@istest
def can_infer_type_of_subtraction_operation():
    type_bindings = {"x": types.int_type, "y": types.int_type}
    subtraction = nodes.sub(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(subtraction, type_bindings=type_bindings))


@istest
def operands_of_sub_operation_must_support_sub():
    type_bindings = {"x": types.none_type, "y": types.none_type}
    subtraction = nodes.sub(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(subtraction, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.NoSuchAttributeError as error:
        assert_equal(nodes.attr(subtraction.left, "__sub__"), error.node)


@istest
def can_infer_type_of_multiplication_operation():
    type_bindings = {"x": types.int_type, "y": types.int_type}
    multiplication = nodes.mul(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(multiplication, type_bindings=type_bindings))


@istest
def operands_of_mul_operation_must_support_mul():
    type_bindings = {"x": types.none_type, "y": types.none_type}
    multiplication = nodes.mul(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(multiplication, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.NoSuchAttributeError as error:
        assert_equal(nodes.attr(multiplication.left, "__mul__"), error.node)
        assert_equal(multiplication.left, ephemeral.root_node(error.node))


@istest
def can_infer_type_of_negation_operation():
    type_bindings = {"x": types.int_type}
    negation = nodes.neg(nodes.ref("x"))
    assert_equal(types.int_type, infer(negation, type_bindings=type_bindings))


@istest
def can_infer_type_of_subscript_using_getitem():
    cls = types.class_type("Blah", [
        types.attr("__getitem__", types.func([types.int_type], types.str_type)),
    ])
    type_bindings = {"x": cls}
    node = nodes.subscript(nodes.ref("x"), nodes.int_literal(4))
    assert_equal(types.str_type, infer(node, type_bindings=type_bindings))


@istest
def can_infer_type_of_slice():
    node = nodes.slice(nodes.str_literal(""), nodes.int_literal(4), nodes.none())
    assert_equal(
        types.slice_type(types.str_type, types.int_type, types.none_type),
        infer(node)
    )


@istest
def can_infer_type_of_subscript_of_list():
    type_bindings = {"x": types.list_type(types.str_type)}
    node = nodes.subscript(nodes.ref("x"), nodes.int_literal(4))
    assert_equal(types.str_type, infer(node, type_bindings=type_bindings))


@istest
def type_of_boolean_and_operation_is_unification_of_operand_types():
    type_bindings = {"x": types.int_type, "y": types.int_type}
    operation = nodes.bool_and(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(operation, type_bindings=type_bindings))


@istest
def type_of_boolean_or_operation_is_unification_of_operand_types():
    type_bindings = {"x": types.int_type, "y": types.int_type}
    operation = nodes.bool_or(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(operation, type_bindings=type_bindings))


@istest
def type_of_boolean_not_operation_is_boolean():
    type_bindings = {"x": types.int_type}
    operation = nodes.bool_not(nodes.ref("x"))
    assert_equal(types.bool_type, infer(operation, type_bindings=type_bindings))


@istest
def value_of_boolean_not_operation_is_type_checked():
    assert_subexpression_is_type_checked(lambda bad_ref: nodes.bool_not(bad_ref))


@istest
def type_of_is_operation_is_boolean():
    type_bindings = {"x": types.object_type, "y": types.str_type}
    operation = nodes.is_(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.bool_type, infer(operation, type_bindings=type_bindings))


@istest
def operands_of_is_operation_are_type_checked():
    assert_subexpression_is_type_checked(lambda bad_ref: nodes.is_(bad_ref, nodes.int_literal(1)))
    assert_subexpression_is_type_checked(lambda bad_ref: nodes.is_(nodes.int_literal(1), bad_ref))
