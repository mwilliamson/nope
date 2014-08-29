from nose.tools import istest, assert_equal

from nope import types, nodes, errors

from .util import infer, create_context, assert_subexpression_is_type_checked


@istest
def can_infer_type_of_addition_operation():
    context = create_context({"x": types.int_type, "y": types.int_type})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(addition, context))


@istest
def cannot_add_int_and_str():
    context = create_context({"x": types.int_type, "y": types.str_type})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(addition.right, error.node)
        assert_equal(types.int_type, error.expected)
        assert_equal(types.str_type, error.actual)


@istest
def operands_of_add_operation_must_support_add():
    context = create_context({"x": types.none_type, "y": types.none_type})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(addition.left, error.node)
        assert_equal("object with method '__add__'", error.expected)
        assert_equal(types.none_type, error.actual)


@istest
def right_hand_operand_must_be_sub_type_of_formal_argument():
    context = create_context({"x": types.int_type, "y": types.object_type})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(addition.right, error.node)
        assert_equal(types.int_type, error.expected)
        assert_equal(types.object_type, error.actual)


@istest
def type_of_add_method_argument_allows_super_type():
    cls = types.scalar_type("Addable", {})
    cls.attrs.add("__add__", types.func([types.object_type], cls))
    
    context = create_context({"x": cls, "y": cls})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(cls, infer(addition, context))


@istest
def add_method_should_only_accept_one_argument():
    cls = types.scalar_type("NotAddable", {})
    cls.attrs.add("__add__", types.func([types.object_type, types.object_type], cls))
    
    context = create_context({"x": cls, "y": cls})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, context)
        assert False, "Expected error"
    except errors.BadSignatureError as error:
        assert_equal(addition.left, error.node)
        assert_equal("__add__ should have exactly 1 argument(s)", str(error))


@istest
def return_type_of_add_can_differ_from_original_type():
    cls = types.scalar_type("Addable", {})
    cls.attrs.add("__add__", types.func([types.object_type], types.object_type))
    
    context = create_context({"x": cls, "y": cls})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.object_type, infer(addition, context))


@istest
def can_infer_type_of_subtraction_operation():
    context = create_context({"x": types.int_type, "y": types.int_type})
    subtraction = nodes.sub(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(subtraction, context))


@istest
def operands_of_sub_operation_must_support_sub():
    context = create_context({"x": types.none_type, "y": types.none_type})
    subtraction = nodes.sub(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(subtraction, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(subtraction.left, error.node)
        assert_equal("object with method '__sub__'", error.expected)
        assert_equal(types.none_type, error.actual)


@istest
def can_infer_type_of_multiplication_operation():
    context = create_context({"x": types.int_type, "y": types.int_type})
    multiplication = nodes.mul(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(multiplication, context))


@istest
def operands_of_mul_operation_must_support_mul():
    context = create_context({"x": types.none_type, "y": types.none_type})
    multiplication = nodes.mul(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(multiplication, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(multiplication.left, error.node)
        assert_equal("object with method '__mul__'", error.expected)
        assert_equal(types.none_type, error.actual)


@istest
def can_infer_type_of_negation_operation():
    context = create_context({"x": types.int_type})
    negation = nodes.neg(nodes.ref("x"))
    assert_equal(types.int_type, infer(negation, context))


@istest
def can_infer_type_of_subscript_using_getitem():
    cls = types.scalar_type("Blah", [
        types.attr("__getitem__", types.func([types.int_type], types.str_type)),
    ])
    context = create_context({"x": cls})
    node = nodes.subscript(nodes.ref("x"), nodes.int(4))
    assert_equal(types.str_type, infer(node, context))


@istest
def can_infer_type_of_subscript_of_list():
    context = create_context({"x": types.list_type(types.str_type)})
    node = nodes.subscript(nodes.ref("x"), nodes.int(4))
    assert_equal(types.str_type, infer(node, context))


@istest
def type_of_boolean_and_operation_is_unification_of_operand_types():
    context = create_context({"x": types.int_type, "y": types.int_type})
    operation = nodes.bool_and(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(operation, context))


@istest
def type_of_boolean_or_operation_is_unification_of_operand_types():
    context = create_context({"x": types.int_type, "y": types.int_type})
    operation = nodes.bool_or(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(operation, context))


@istest
def type_of_boolean_not_operation_is_boolean():
    context = create_context({"x": types.int_type})
    operation = nodes.bool_not(nodes.ref("x"))
    assert_equal(types.boolean_type, infer(operation, context))


@istest
def value_of_boolean_not_operation_is_type_checked():
    assert_subexpression_is_type_checked(lambda bad_ref: nodes.bool_not(bad_ref))
