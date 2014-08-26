from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.context import Context

from .util import assert_type_mismatch, update_context, SingleScopeReferences


@istest
def can_infer_type_of_function_with_no_args_and_no_return():
    node = nodes.func("f", signature=nodes.signature(), args=nodes.Arguments([]), body=[])
    assert_equal(types.func([], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_args_and_no_return():
    signature = nodes.signature(args=[
        nodes.signature_arg(nodes.ref("int")),
        nodes.signature_arg(nodes.ref("str")),
    ])
    args = nodes.arguments([
        nodes.argument("x"),
        nodes.argument("y"),
    ])
    node = nodes.func("f", signature=signature, args=args, body=[])
    assert_equal(types.func([types.int_type, types.str_type], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_no_args_and_return_annotation():
    node = nodes.func(
        "f",
        nodes.signature(returns=nodes.ref("int")),
        args=nodes.Arguments([]),
        body=[
            nodes.ret(nodes.int(4))
        ]
    )
    assert_equal(types.func([], types.int_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_named_arg():
    signature = nodes.signature(args=[
        nodes.signature_arg("message", nodes.ref("int")),
    ])
    args = nodes.arguments([
        nodes.argument("message"),
    ])
    node = nodes.func("f", signature=signature, args=args, body=[])
    assert_equal(
        types.func([types.func_arg("message", types.int_type)], types.none_type),
        _infer_func_type(node)
    )


@istest
def type_mismatch_if_return_type_is_incorrect():
    return_node = nodes.ret(nodes.string("!"))
    node = nodes.func(
        "f",
        nodes.signature(returns=nodes.ref("int")),
        args=nodes.arguments([]),
        body=[return_node],
    )
    assert_type_mismatch(lambda: _infer_func_type(node), expected=types.int_type, actual=types.str_type, node=return_node)


@istest
def type_error_if_return_is_missing():
    node = nodes.func(
        "f",
        nodes.signature(returns=nodes.ref("int")),
        args=nodes.arguments([]),
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
    signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("int")
    )
    args = nodes.arguments([nodes.argument("x")])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.func("f", signature, args, body)
    assert_equal(types.func([types.int_type], types.int_type), _infer_func_type(node))


def _infer_func_type(func_node):
    context = Context(SingleScopeReferences(), {}).enter_module()
    context.update_type(nodes.ref("int"), types.meta_type(types.int_type))
    context.update_type(nodes.ref("str"), types.meta_type(types.str_type))
    update_context(func_node, context)
    return context.lookup(func_node)
