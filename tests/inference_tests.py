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
