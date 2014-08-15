from nose.tools import istest, assert_equal, assert_raises

from nope import types, nodes, inference, errors
from nope.inference import infer as _infer, update_context, ephemeral
from nope.context import bound_context, new_module_context, Context, Variable


def infer(node, context=None):
    if context is None:
        context = bound_context({})
    return _infer(node, context)


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
def can_infer_type_of_variable_reference():
    assert_equal(types.int_type, infer(nodes.ref("x"), bound_context({"x": types.int_type})))


@istest
def type_error_if_ref_to_undefined_variable():
    node = nodes.ref("x")
    try:
        infer(node, bound_context({}))
        assert False, "Expected error"
    except errors.UndefinedNameError as error:
        assert_equal(node, error.node)
        assert_equal("name 'x' is not defined", str(error))


@istest
def can_infer_type_of_list_of_ints():
    assert_equal(types.list_type(types.int_type), infer(nodes.list([nodes.int(1), nodes.int(42)])))
    

@istest
def empty_list_has_elements_of_type_bottom():
    assert_equal(types.list_type(types.bottom_type), infer(nodes.list([])))


@istest
def can_infer_type_of_call():
    context = bound_context({"f": types.func([types.str_type], types.int_type)})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def object_can_be_called_if_it_has_call_magic_method():
    cls = types.ScalarType("Blah", {
        "__call__": types.func([types.str_type], types.int_type)
    })
    context = bound_context({"f": cls})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def callee_must_be_function_or_have_call_magic_method():
    cls = types.ScalarType("Blah", {})
    context = bound_context({"f": cls})
    callee_node = nodes.ref("f")
    try:
        infer(nodes.call(callee_node, []), context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(callee_node, error.node)
        assert_equal("callable object", error.expected)
        assert_equal(cls, error.actual)


@istest
def call_attribute_must_be_function():
    cls = types.ScalarType("Blah", {"__call__": types.int_type})
    context = bound_context({"f": cls})
    callee_node = nodes.ref("f")
    try:
        infer(nodes.call(callee_node, []), context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(callee_node, ephemeral.root_node(error.node))
        assert_equal(nodes.attr(callee_node, "__call__"), ephemeral.underlying_node(error.node))
        assert_equal("callable object", error.expected)
        assert_equal(types.int_type, error.actual)


@istest
def call_arguments_must_match():
    context = bound_context({"f": types.func([types.str_type], types.int_type)})
    arg_node = nodes.int(4)
    node = nodes.call(nodes.ref("f"), [arg_node])
    _assert_type_mismatch(
        lambda: infer(node, context),
        expected=types.str_type,
        actual=types.int_type,
        node=arg_node,
    )


@istest
def call_arguments_length_must_match():
    context = bound_context({"f": types.func([types.str_type], types.int_type)})
    node = nodes.call(nodes.ref("f"), [])
    try:
        infer(node, context)
        assert False, "Expected error"
    except errors.ArgumentsLengthError as error:
        assert_equal(1, error.expected)
        assert_equal(0, error.actual)
        assert error.node is node


@istest
def can_infer_type_of_attribute():
    context = bound_context({"x": types.str_type})
    assert_equal(
        types.func([types.str_type], types.int_type),
        infer(nodes.attr(nodes.ref("x"), "find"), context)
    )


@istest
def type_error_if_attribute_does_not_exist():
    context = bound_context({"x": types.str_type})
    node = nodes.attr(nodes.ref("x"), "swizzlify")
    try:
        infer(node, context)
        assert False, "Expected error"
    except errors.AttributeError as error:
        assert_equal("str object has no attribute swizzlify", str(error))
        assert error.node is node


@istest
def can_infer_type_of_addition_operation():
    context = bound_context({"x": types.int_type, "y": types.int_type})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(addition, context))


@istest
def cannot_add_int_and_str():
    context = bound_context({"x": types.int_type, "y": types.str_type})
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
    context = bound_context({"x": types.none_type, "y": types.none_type})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(addition.left, error.node)
        assert_equal("type with __add__", error.expected)
        assert_equal(types.none_type, error.actual)


@istest
def right_hand_operand_must_be_sub_type_of_formal_argument():
    context = bound_context({"x": types.int_type, "y": types.object_type})
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
    cls = types.ScalarType("Addable", {})
    cls.attrs["__add__"] = types.func([types.object_type], cls)
    
    context = bound_context({"x": cls, "y": cls})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(cls, infer(addition, context))


@istest
def add_method_should_only_accept_one_argument():
    cls = types.ScalarType("NotAddable", {})
    cls.attrs["__add__"] = types.func([types.object_type, types.object_type], cls)
    
    context = bound_context({"x": cls, "y": cls})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(addition, context)
        assert False, "Expected error"
    except errors.BadSignatureError as error:
        assert_equal(addition.left, error.node)
        assert_equal("__add__ should have exactly 1 argument(s)", str(error))


@istest
def return_type_of_add_can_differ_from_original_type():
    cls = types.ScalarType("Addable", {})
    cls.attrs["__add__"] = types.func([types.object_type], types.object_type)
    
    context = bound_context({"x": cls, "y": cls})
    addition = nodes.add(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.object_type, infer(addition, context))


@istest
def can_infer_type_of_subtraction_operation():
    context = bound_context({"x": types.int_type, "y": types.int_type})
    subtraction = nodes.sub(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(subtraction, context))


@istest
def operands_of_sub_operation_must_support_sub():
    context = bound_context({"x": types.none_type, "y": types.none_type})
    subtraction = nodes.sub(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(subtraction, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(subtraction.left, error.node)
        assert_equal("type with __sub__", error.expected)
        assert_equal(types.none_type, error.actual)


@istest
def can_infer_type_of_multiplication_operation():
    context = bound_context({"x": types.int_type, "y": types.int_type})
    multiplication = nodes.mul(nodes.ref("x"), nodes.ref("y"))
    assert_equal(types.int_type, infer(multiplication, context))


@istest
def operands_of_mul_operation_must_support_mul():
    context = bound_context({"x": types.none_type, "y": types.none_type})
    multiplication = nodes.mul(nodes.ref("x"), nodes.ref("y"))
    try:
        infer(multiplication, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(multiplication.left, error.node)
        assert_equal("type with __mul__", error.expected)
        assert_equal(types.none_type, error.actual)


@istest
def can_infer_type_of_negation_operation():
    context = bound_context({"x": types.int_type})
    negation = nodes.neg(nodes.ref("x"))
    assert_equal(types.int_type, infer(negation, context))


@istest
def can_infer_type_of_subscript_using_getitem():
    cls = types.ScalarType("Blah", {
        "__getitem__": types.func([types.int_type], types.str_type)
    })
    context = bound_context({"x": cls})
    node = nodes.subscript(nodes.ref("x"), nodes.int(4))
    assert_equal(types.str_type, infer(node, context))


@istest
def can_infer_type_of_subscript_of_list():
    context = bound_context({"x": types.list_type(types.str_type)})
    node = nodes.subscript(nodes.ref("x"), nodes.int(4))
    assert_equal(types.str_type, infer(node, context))

    

@istest
def can_infer_type_of_function_with_no_args_and_no_return():
    node = nodes.func("f", args=nodes.Arguments([]), return_annotation=None, body=[])
    assert_equal(types.func([], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_args_and_no_return():
    args = nodes.arguments([
        nodes.argument("x", nodes.ref("int")),
        nodes.argument("y", nodes.ref("str")),
    ])
    node = nodes.func("f", args=args, return_annotation=None, body=[])
    assert_equal(types.func([types.int_type, types.str_type], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_no_args_and_return_annotation():
    node = nodes.func(
        "f",
        args=nodes.Arguments([]),
        return_annotation=nodes.ref("int"),
        body=[
            nodes.ret(nodes.int(4))
        ]
    )
    assert_equal(types.func([], types.int_type), _infer_func_type(node))


@istest
def type_mismatch_if_return_type_is_incorrect():
    return_node = nodes.ret(nodes.string("!"))
    node = nodes.func(
        "f",
        args=nodes.arguments([]),
        return_annotation=nodes.ref("int"),
        body=[return_node],
    )
    _assert_type_mismatch(lambda: _infer_func_type(node), expected=types.int_type, actual=types.str_type, node=return_node)


@istest
def type_error_if_return_is_missing():
    node = nodes.func(
        "f",
        args=nodes.arguments([]),
        return_annotation=nodes.ref("int"),
        body=[],
    )
    try:
        _infer_func_type(node)
        assert False, "Expected error"
    except errors.MissingReturnError as error:
        assert_equal(node, error.node)
        assert_equal("Function must return value of type 'int'", str(error))


@istest
def function_adds_arguments_to_context():
    args = nodes.arguments([
        nodes.argument("x", nodes.ref("int")),
    ])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.func("f", args=args, return_annotation=nodes.ref("int"), body=body)
    assert_equal(types.func([types.int_type], types.int_type), _infer_func_type(node))


@istest
def assignment_adds_variable_to_context():
    node = nodes.assign(["x"], nodes.int(1))
    context = bound_context({"x": None})
    update_context(node, context)
    assert_equal(types.int_type, context.lookup("x"))


@istest
def assignment_to_list_allows_subtype():
    node = nodes.assign([nodes.subscript(nodes.ref("x"), nodes.int(0))], nodes.string("Hello"))
    context = bound_context({"x": types.list_type(types.object_type)})
    update_context(node, context)


@istest
def assignment_to_list_does_not_allow_supertype():
    target_node = nodes.subscript(nodes.ref("x"), nodes.int(0))
    value_node = nodes.ref("y")
    node = nodes.assign([target_node], value_node)
    context = bound_context({
        "x": types.list_type(types.str_type),
        "y": types.object_type,
    })
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(target_node, error.node)
        assert_equal(types.object_type, error.expected)
        assert_equal(types.str_type, error.actual)


@istest
def variables_cannot_change_type():
    node = nodes.assign(["x"], nodes.int(1))
    context = bound_context({"x": types.none_type})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(node, error.node)


@istest
def variables_cannot_change_type_even_if_variable_is_potentially_unbound():
    node = nodes.assign(["x"], nodes.int(1))
    context = Context({"x": Variable(types.none_type, is_bound=False)})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(node, error.node)


@istest
def variables_can_be_reassigned_if_type_is_consistent():
    node = nodes.assign(["x"], nodes.int(1))
    context = bound_context({"x": types.object_type})
    update_context(node, context)
    assert_equal(types.object_type, context.lookup("x"))


@istest
def variables_are_shadowed_in_defs():
    node = nodes.func("g", nodes.args([]), None, [
        nodes.assign(["x"], nodes.string("Hello")),
        nodes.expression_statement(nodes.call(nodes.ref("f"), [nodes.ref("x")])),
    ])
    
    context = bound_context({
        "g": None,
        "f": types.func([types.str_type], types.none_type),
        "x": types.int_type,
    })
    update_context(node, context)
    
    assert_equal(types.int_type, context.lookup("x"))


@istest
def local_variables_cannot_be_used_before_assigned():
    usage_node = nodes.ref("x")
    node = nodes.func("g", nodes.args([]), None, [
        nodes.expression_statement(nodes.call(nodes.ref("f"), [usage_node])),
        nodes.assign("x", nodes.string("Hello")),
    ])
    
    context = bound_context({
        "f": types.func([types.str_type], types.none_type),
        "x": types.int_type,
    })
    try:
        update_context(node, context)
        assert False, "Expected UnboundLocalError"
    except errors.UnboundLocalError as error:
        assert_equal("local variable x referenced before assignment", str(error))
        assert error.node is usage_node


@istest
def if_statement_has_condition_type_checked():
    ref_node = nodes.ref("y")
    node = nodes.if_else(ref_node, [], [])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def if_statement_has_true_body_type_checked():
    ref_node = nodes.ref("y")
    node = nodes.if_else(
        nodes.int(1),
        [nodes.expression_statement(ref_node)],
        [],
    )
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def if_statement_has_false_body_type_checked():
    ref_node = nodes.ref("y")
    node = nodes.if_else(
        nodes.int(1),
        [],
        [nodes.expression_statement(ref_node)],
    )
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def assignment_in_both_branches_of_if_statement_is_added_to_context():
    node = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(1))],
        [nodes.assign("x", nodes.int(2))],
    )
    context = bound_context({"x": None})
    update_context(node, context)
    assert_equal(types.int_type, context.lookup("x"))


@istest
def type_of_variable_is_unified_if_branches_of_if_else_use_different_types():
    node = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(1))],
        [nodes.assign("x", nodes.string("blah"))],
    )
    context = bound_context({"x": None})
    update_context(node, context)
    assert_equal(types.object_type, context.lookup("x"))


@istest
def variable_remains_unbound_if_only_set_in_one_branch_of_if_else():
    node = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(1))],
        [],
    )
    context = bound_context({"x": None})
    update_context(node, context)
    assert not context.is_bound("x")
    assert_equal(types.int_type, context.lookup("x", allow_unbound=True))


@istest
def while_loop_has_condition_type_checked():
    condition_node = nodes.ref("x")
    node = nodes.while_loop(condition_node, [])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(condition_node, error.node)


@istest
def while_loop_has_body_type_checked():
    body_node = nodes.ref("x")
    node = nodes.while_loop(nodes.boolean(True), [nodes.expression_statement(body_node)])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(body_node, error.node)


@istest
def while_loop_has_else_body_type_checked():
    body_node = nodes.ref("x")
    node = nodes.while_loop(nodes.boolean(True), [], [nodes.expression_statement(body_node)])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(body_node, error.node)


@istest
def type_of_variable_remains_undefined_if_set_in_while_loop_body():
    node = nodes.while_loop(nodes.boolean(True), [
        nodes.assign([nodes.ref("x")], nodes.int(2))
    ])
    context = bound_context({"x": None})
    update_context(node, context)
    assert not context.is_bound("x")
    assert_equal(types.int_type, context.lookup("x", allow_unbound=True))


@istest
def for_statement_accepts_iterable_with_iter_method():
    cls = types.ScalarType("Blah", {})
    cls.attrs["__iter__"] = types.func([], types.iterator(types.str_type))
    
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [])
    
    context = bound_context({
        "x": None,
        "xs": cls,
    })
    
    update_context(node, context)
    
    assert_equal(types.str_type, context.lookup("x", allow_unbound=True))


@istest
def for_statement_accepts_iterable_with_getitem_method():
    cls = types.ScalarType("Blah", {})
    cls.attrs["__getitem__"] = types.func([types.int_type], types.str_type)
    
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [])
    
    context = bound_context({
        "x": None,
        "xs": cls,
    })
    
    update_context(node, context)
    
    assert_equal(types.str_type, context.lookup("x", allow_unbound=True))


@istest
def for_statement_has_iterable_type_checked():
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def for_statement_requires_iterable_to_have_iter_method():
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({"x": None, "xs": types.int_type}))
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(ref_node, error.node)
        assert_equal("iterable type", error.expected)
        assert_equal(types.int_type, error.actual)


@istest
def iter_method_must_take_no_arguments():
    cls = types.ScalarType("Blah", {})
    cls.attrs["__iter__"] = types.func([types.str_type], types.iterable(types.str_type))
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({"x": None, "xs": cls}))
        assert False, "Expected error"
    except errors.BadSignatureError as error:
        assert_equal(ref_node, error.node)


@istest
def iter_method_must_return_iterator():
    cls = types.ScalarType("Blah", {})
    cls.attrs["__iter__"] = types.func([], types.iterable(types.str_type))
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({"x": None, "xs": cls}))
        assert False, "Expected error"
    except errors.BadSignatureError as error:
        assert_equal(ref_node, error.node)


@istest
def for_statement_target_can_be_supertype_of_iterable_element_type():
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.subscript(nodes.ref("ys"), nodes.int(0)), ref_node, [])
    
    update_context(node, bound_context({
        "xs": types.list_type(types.int_type),
        "ys": types.list_type(types.object_type),
    }))


@istest
def for_statement_target_cannot_be_strict_subtype_of_iterable_element_type():
    target_node = nodes.subscript(nodes.ref("ys"), nodes.int(0))
    iterable_node = nodes.ref("xs")
    node = nodes.for_loop(target_node, iterable_node, [])
    
    try:
        update_context(node, bound_context({
            "xs": types.list_type(types.object_type),
            "ys": types.list_type(types.int_type),
        }))
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(target_node, error.node)
        assert_equal(types.object_type, error.expected)
        assert_equal(types.int_type, error.actual)


@istest
def for_statement_target_can_be_variable():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [])
    
    # Unassigned case
    update_context(node, bound_context({
        "x": None,
        "xs": types.list_type(types.str_type),
    }))
    # Assigned case
    update_context(node, bound_context({
        "x": types.str_type,
        "xs": types.list_type(types.str_type),
    }))


@istest
def body_of_for_loop_is_type_checked():
    bad_ref = nodes.ref("bad")
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [
        nodes.expression_statement(bad_ref),
    ])
    
    try:
        update_context(node, bound_context({
            "x": None,
            "xs": types.list_type(types.str_type),
        }))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(bad_ref, error.node)


@istest
def else_body_of_for_loop_is_type_checked():
    bad_ref = nodes.ref("bad")
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [], [
        nodes.expression_statement(bad_ref),
    ])
    
    try:
        update_context(node, bound_context({
            "x": None,
            "xs": types.list_type(types.str_type),
        }))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(bad_ref, error.node)


@istest
def type_of_variable_remains_unbound_if_only_assigned_to_in_for_loop():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [
        nodes.assign("y", nodes.none()),
    ])
    
    context = bound_context({
        "x": None,
        "xs": types.list_type(types.str_type),
        "y": None,
    })
    update_context(node, context)
    assert not context.is_bound("y")
    assert_equal(types.none_type, context.lookup("y", allow_unbound=True))


@istest
def break_is_not_valid_in_module():
    node = nodes.break_statement()
    context = bound_context({})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_valid_in_for_loop():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [nodes.break_statement()])
    context = bound_context({"x": types.int_type, "xs": types.list_type(types.int_type)})
    update_context(node, context)


@istest
def break_is_valid_in_if_else_in_for_loop():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [
        nodes.if_else(nodes.ref("x"), [nodes.break_statement()], []),
    ])
    context = bound_context({"x": types.int_type, "xs": types.list_type(types.int_type)})
    update_context(node, context)


@istest
def continue_is_not_valid_in_module():
    node = nodes.continue_statement()
    context = bound_context({})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'continue' outside loop", str(error))


@istest
def raise_value_can_be_instance_of_exception():
    context = bound_context({"error": types.exception_type})
    update_context(nodes.raise_statement(nodes.ref("error")), context)


@istest
def raise_value_can_be_instance_of_subtype_of_exception():
    cls = types.ScalarType("BlahError", {}, base_classes=[types.exception_type])
    context = bound_context({"error": cls})
    update_context(nodes.raise_statement(nodes.ref("error")), context)


@istest
def raise_value_cannot_be_non_subtype_of_exception():
    context = bound_context({"error": types.object_type})
    ref_node = nodes.ref("error")
    try:
        update_context(nodes.raise_statement(ref_node), context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(ref_node, error.node)


@istest
def check_generates_type_lookup_for_all_expressions():
    int_ref_node = nodes.ref("a")
    int_node = nodes.int(3)
    str_node = nodes.string("Hello")
    
    module_node = nodes.module([
        nodes.assign(["a"], int_node),
        nodes.func("f", nodes.args([]), None, [
            nodes.assign("b", int_ref_node),
            nodes.assign("c", str_node),
        ]),
    ])
    
    context = bound_context({})
    module, type_lookup = inference.check(module_node)
    assert_equal(types.int_type, type_lookup.type_of(int_node))
    assert_equal(types.int_type, type_lookup.type_of(int_ref_node))
    assert_equal(types.str_type, type_lookup.type_of(str_node))


@istest
def module_exports_are_specified_using_all():
    module_node = nodes.module([
        nodes.assign(["__all__"], nodes.list([nodes.string("x"), nodes.string("z")])),
        nodes.assign(["x"], nodes.string("one")),
        nodes.assign(["y"], nodes.string("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    context = bound_context({})
    module, type_lookup = inference.check(module_node)
    assert_equal(types.str_type, module.attrs["x"])
    assert_raises(KeyError, lambda: module.attrs["y"])
    assert_equal(types.int_type, module.attrs["z"])


@istest
def module_exports_default_to_values_without_leading_underscore_if_all_is_not_specified():
    module_node = nodes.module([
        nodes.assign(["x"], nodes.string("one")),
        nodes.assign(["_y"], nodes.string("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    context = bound_context({})
    module, type_lookup = inference.check(module_node)
    assert_equal(types.str_type, module.attrs["x"])
    assert_raises(KeyError, lambda: module.attrs["_y"])
    assert_equal(types.int_type, module.attrs["z"])


@istest
def can_import_local_module_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message.py": _module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["message"])
    
    assert_equal(types.str_type, context.lookup("message").attrs["value"])


@istest
def can_import_local_package_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": _module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["message"])
    
    assert_equal(types.str_type, context.lookup("message").attrs["value"])


@istest
def importing_module_in_package_mutates_that_package():
    node = nodes.Import([nodes.import_alias("messages.hello", None)])
    messages_module = _module({})
    hello_module = _module({"value": types.str_type})
    
    source_tree = FakeSourceTree({
        "root/messages/__init__.py": messages_module,
        "root/messages/hello.py": hello_module,
    })
    
    context = _update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["messages"])
    
    assert_equal(hello_module, context.lookup("messages").attrs["hello"])


@istest
def can_use_aliases_with_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", "m")])
    
    source_tree = FakeSourceTree({
        "root/message.py": _module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["m"])
    
    assert_equal(types.str_type, context.lookup("m").attrs["value"])
    assert_raises(KeyError, lambda: context.lookup("message"))


@istest
def cannot_import_local_packages_if_not_in_executable():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": _module({"value": types.str_type})
    })
    
    try:
        _update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=False,
            declared_names=["message"])
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_is_ambiguous():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": _module({"value": types.str_type}),
        "root/message.py": _module({"value": types.str_type})
    })
    
    try:
        _update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=True,
            declared_names=["message"])
        assert False
    except errors.ImportError as error:
        assert_equal("Import is ambiguous: the module 'message.py' and the package 'message/__init__.py' both exist", str(error))
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_cannot_be_resolved():
    node = nodes.Import([nodes.import_alias("message.value", None)])
    source_tree = FakeSourceTree({
        "root/message/__init__.py": _module({}),
    })
    
    try:
        _update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=True,
            declared_names=["message"])
        assert False
    except errors.ImportError as error:
        assert_equal("Could not find module 'message.value'", str(error))
        assert_equal(node, error.node)


@istest
def error_is_raised_if_value_in_package_has_same_name_as_module():
    value_node = nodes.assign("x", nodes.int(1))
    node = nodes.Module([value_node], is_executable=False)
    source_tree = FakeSourceTree({
        "root/x.py": _module({}),
    })
    
    try:
        inference.check(node, source_tree, module_path="root/__init__.py")
        assert False, "Expected error"
    except errors.ImportedValueRedeclaration as error:
        assert_equal(value_node, error.node)
        assert_equal("Cannot declare value 'x' in module scope due to child module with the same name", str(error))


@istest
def values_can_have_same_name_as_child_module_if_they_are_not_in_module_scope():
    value_node = nodes.assign("x", nodes.int(1))
    node = nodes.Module([
        nodes.func("f", nodes.args([]), None, [value_node])
    ], is_executable=False)
    source_tree = FakeSourceTree({
        "root/x.py": _module({}),
    })
    
    inference.check(node, source_tree, module_path="root/__init__.py")


@istest
def value_in_package_can_have_same_name_as_module_if_it_is_that_module():
    value_node = nodes.import_from(["."], [nodes.import_alias("x", None)])
    node = nodes.Module([value_node], is_executable=False)
    source_tree = FakeSourceTree({
        "root/__init__.py": _module({}),
        "root/x.py": _module({}),
    })
    
    inference.check(node, source_tree, module_path="root/__init__.py")


@istest
def module_can_have_value_with_same_name_as_sibling_module():
    value_node = nodes.assign("x", nodes.int(1))
    node = nodes.Module([value_node], is_executable=False)
    source_tree = FakeSourceTree({
        "root/x.py": _module({}),
    })
    
    inference.check(node, source_tree, module_path="root/y.py")


@istest
def can_import_value_from_relative_module_using_import_from_syntax():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", None)])
    
    source_tree = FakeSourceTree({
        "root/message.py": _module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree,
        module_path="root/main.py",
        declared_names=["value"])
    
    assert_equal(types.str_type, context.lookup("value"))
    assert_raises(KeyError, lambda: context.lookup("message"))


@istest
def can_import_relative_module_using_import_from_syntax():
    node = nodes.import_from(["."], [nodes.import_alias("message", None)])
    root_module = _module({})
    message_module = _module({"value": types.str_type})
    
    source_tree = FakeSourceTree({
        "root/__init__.py": root_module,
        "root/message.py": message_module,
    })
    
    context = _update_blank_context(node, source_tree,
        module_path="root/main.py",
        declared_names=["message"])
    
    assert_equal(types.str_type, context.lookup("message").attrs["value"])
    assert_equal(message_module, root_module.attrs["message"])


@istest
def can_import_relative_module_using_import_from_syntax_with_alias():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", "v")])
    
    source_tree = FakeSourceTree({
        "root/message.py": _module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree,
        module_path="root/main.py",
        declared_names=["v"])
    
    assert_equal(types.str_type, context.lookup("v"))
    assert_raises(KeyError, lambda: context.lookup("value"))
    assert_raises(KeyError, lambda: context.lookup("message"))


class FakeSourceTree(object):
    def __init__(self, modules):
        self._modules = modules
    
    def import_module(self, path):
        return self._modules.get(path)
    
    def __contains__(self, value):
        return value in self._modules


def _infer_func_type(func_node):
    context = new_module_context({func_node.name: None})
    update_context(func_node, context)
    return context.lookup(func_node.name)


def _update_blank_context(node, *args, declared_names=[], **kwargs):
    context = bound_context(dict((name, None) for name in declared_names))
    update_context(node, context, *args, **kwargs)
    return context


def _module(attrs):
    return types.Module("generic_module_name", attrs)


def _assert_type_mismatch(func, expected, actual, node):
    try:
        func()
        assert False, "Expected type mismatch"
    except errors.TypeMismatchError as mismatch:
        assert_equal(expected, mismatch.expected)
        assert_equal(actual, mismatch.actual)
        assert mismatch.node is node
