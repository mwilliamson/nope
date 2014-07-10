from nose.tools import istest, assert_equal

from nope import types, nodes, inference
from nope.inference import infer, Context, module_context


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
def can_infer_type_of_function_with_no_args_and_no_return():
    node = nodes.func(args=nodes.Arguments([]), return_annotation=None, body=[])
    assert_equal(types.func([], types.none_type), infer(node))


@istest
def can_infer_type_of_function_with_args_and_no_return():
    args = nodes.arguments([
        nodes.argument("x", nodes.ref("int")),
        nodes.argument("y", nodes.ref("str")),
    ])
    node = nodes.func(args=args, return_annotation=None, body=[])
    assert_equal(types.func([types.int, types.str], types.none_type), infer(node, module_context))


@istest
def can_infer_type_of_function_with_no_args_and_return_annotation():
    node = nodes.func(
        args=nodes.Arguments([]),
        return_annotation=nodes.ref("int"),
        body=[
            nodes.ret(nodes.int(4))
        ]
    )
    assert_equal(types.func([], types.int), infer(node, module_context))


@istest
def can_infer_type_of_function_with_args_and_no_return():
    node = nodes.func(
        args=nodes.arguments([]),
        return_annotation=nodes.ref("int"),
        body=[
            nodes.ret(nodes.str("!")),
        ],
    )
    _assert_type_mismatch(lambda: infer(node, module_context), expected=types.int, actual=types.str)


def _assert_type_mismatch(func, expected, actual):
    try:
        func()
        assert False, "Expected type mismatch"
    except inference.TypeMismatchError as mismatch:
        assert_equal(expected, mismatch.expected)
        assert_equal(actual, mismatch.actual)
