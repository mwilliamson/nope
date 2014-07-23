from nose.tools import istest, assert_equal

from nope import types, nodes, inference
from nope.inference import infer as _infer, Context, module_context, new_module_context, update_context


def infer(node, context=None):
    if context is None:
        context = Context({})
    return _infer(node, context)


@istest
def can_infer_type_of_none():
    assert_equal(types.none_type, infer(nodes.none()))


@istest
def can_infer_type_of_int_literal():
    assert_equal(types.int, infer(nodes.int("4")))


@istest
def can_infer_type_of_str_literal():
    assert_equal(types.str, infer(nodes.str("!")))


@istest
def can_infer_type_of_variable_reference():
    assert_equal(types.int, infer(nodes.ref("x"), Context({"x": types.int})))


@istest
def can_infer_type_of_call():
    context = Context({"f": types.func([types.str], types.int)})
    assert_equal(types.int, infer(nodes.call(nodes.ref("f"), [nodes.str("")]), context))


@istest
def call_arguments_must_match():
    context = Context({"f": types.func([types.str], types.int)})
    _assert_type_mismatch(
        lambda: infer(nodes.call(nodes.ref("f"), [nodes.int(4)]), context),
        expected=types.str,
        actual=types.int,
    )


@istest
def call_arguments_length_must_match():
    context = Context({"f": types.func([types.str], types.int)})
    try:
        infer(nodes.call(nodes.ref("f"), []), context)
        assert False, "Expected error"
    except inference.ArgumentsLengthError as error:
        assert_equal(1, error.expected)
        assert_equal(0, error.actual)
    

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
    assert_equal(types.func([types.int, types.str], types.none_type), _infer_func_type(node))


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
    assert_equal(types.func([], types.int), _infer_func_type(node))


@istest
def type_mismatch_if_return_type_is_incorrect():
    node = nodes.func(
        "f",
        args=nodes.arguments([]),
        return_annotation=nodes.ref("int"),
        body=[
            nodes.ret(nodes.str("!")),
        ],
    )
    _assert_type_mismatch(lambda: _infer_func_type(node), expected=types.int, actual=types.str)


@istest
def function_adds_arguments_to_context():
    args = nodes.arguments([
        nodes.argument("x", nodes.ref("int")),
    ])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.func("f", args=args, return_annotation=nodes.ref("int"), body=body)
    assert_equal(types.func([types.int], types.int), _infer_func_type(node))


@istest
def assignment_adds_variable_to_context():
    node = nodes.assign(["x"], nodes.int(1))
    context = Context({})
    update_context(node, context)
    assert_equal(types.int, context.lookup("x"))


@istest
def variables_are_shadowed_in_defs():
    node = nodes.func("g", nodes.args([]), None, [
        nodes.assign(["x"], nodes.str("Hello")),
        nodes.expression_statement(nodes.call(nodes.ref("f"), [nodes.ref("x")])),
    ])
    
    context = Context({
        "f": types.func([types.str], types.none_type),
        "x": types.int,
    })
    update_context(node, context)
    
    assert_equal(types.int, context.lookup("x"))


@istest
def local_variables_cannot_be_used_before_assigned():
    node = nodes.func("g", nodes.args([]), None, [
        nodes.expression_statement(nodes.call(nodes.ref("f"), [nodes.ref("x")])),
        nodes.assign("x", nodes.str("Hello")),
    ])
    
    context = Context({
        "f": types.func([types.str], types.none_type),
        "x": types.int,
    })
    try:
        update_context(node, context)
        assert False, "Expected UnboundLocalError"
    except inference.UnboundLocalError as error:
        assert_equal("local variable x referenced before assignment", str(error))


def _infer_func_type(func_node):
    context = new_module_context()
    update_context(func_node, context)
    return context.lookup(func_node.name)


def _assert_type_mismatch(func, expected, actual):
    try:
        func()
        assert False, "Expected type mismatch"
    except inference.TypeMismatchError as mismatch:
        assert_equal(expected, mismatch.expected)
        assert_equal(actual, mismatch.actual)
