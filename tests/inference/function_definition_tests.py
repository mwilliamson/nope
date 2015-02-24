from nose.tools import istest, assert_equal

from nope import types, nodes, errors

from .util import assert_type_mismatch, update_context


@istest
def can_infer_type_of_function_with_no_args_and_no_return():
    node = nodes.func("f", args=nodes.Arguments([]), body=[])
    assert_equal(types.func([], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_explicit_signature():
    signature = nodes.signature(args=[], returns=nodes.ref("none"))
    args = nodes.arguments([])
    node = nodes.typed(signature, nodes.func("f", args=args, body=[]))
    assert_equal(types.func([], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_explicit_signature_of_aliased_function_type():
    args = nodes.arguments([])
    node = nodes.typed(nodes.ref("Action"), nodes.func("f", args=args, body=[]))
    type_bindings = {
        "Action": types.meta_type(types.func([], types.none_type))
    }
    assert_equal(types.func([], types.none_type), _infer_func_type(node, type_bindings))


@istest
def can_infer_type_of_function_with_args_and_no_return():
    signature = nodes.signature(
        args=[
            nodes.signature_arg(nodes.ref("int")),
            nodes.signature_arg(nodes.ref("str")),
        ],
        returns=nodes.ref("none"),
    )
    args = nodes.arguments([
        nodes.argument("x"),
        nodes.argument("y"),
    ])
    node = nodes.typed(signature, nodes.func("f", args=args, body=[]))
    assert_equal(types.func([types.int_type, types.str_type], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_no_args_and_return_annotation():
    node = nodes.typed(
        nodes.signature(returns=nodes.ref("int")),
        nodes.func(
            "f",
            args=nodes.arguments([]),
            body=[
                nodes.ret(nodes.int_literal(4))
            ]
        )
    )
    assert_equal(types.func([], types.int_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_named_arg():
    signature = nodes.signature(
        args=[
            nodes.signature_arg("message", nodes.ref("int")),
        ],
        returns=nodes.ref("none")
    )
    args = nodes.arguments([
        nodes.argument("message"),
    ])
    node = nodes.typed(signature, nodes.func("f", args=args, body=[]))
    assert_equal(
        types.func([types.func_arg("message", types.int_type)], types.none_type),
        _infer_func_type(node)
    )


@istest
def can_infer_type_of_function_with_optional_arg():
    signature = nodes.signature(
        args=[
            nodes.signature_arg(nodes.ref("int"), optional=True),
        ],
        returns=nodes.ref("none")
    )
    args = nodes.arguments([
        nodes.argument("x", optional=True),
    ])
    node = nodes.typed(signature, nodes.func("f", args=args, body=[]))
    assert_equal(
        types.func([types.func_arg(None, types.int_type, optional=True)], types.none_type),
        _infer_func_type(node)
    )


@istest
def type_mismatch_if_return_type_is_incorrect():
    return_node = nodes.ret(nodes.str_literal("!"))
    node = nodes.typed(
        nodes.signature(returns=nodes.ref("int")),
        nodes.func(
            "f",
            args=nodes.arguments([]),
            body=[return_node],
        )
    )
    assert_type_mismatch(lambda: _infer_func_type(node), expected=types.int_type, actual=types.str_type, node=return_node)


@istest
def type_error_if_return_is_missing():
    node = nodes.typed(
        nodes.signature(returns=nodes.ref("int")),
        nodes.func(
            "f",
            args=nodes.arguments([]),
            body=[],
        )
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
    node = nodes.typed(signature, nodes.func("f", args, body))
    assert_equal(types.func([types.int_type], types.int_type), _infer_func_type(node))


@istest
def argument_type_in_signature_is_unioned_with_none_if_argument_is_optional():
    signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("int")
    )
    args = nodes.arguments([nodes.argument("x", optional=True)])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.typed(signature, nodes.func("f", args, body))
    try:
        _infer_func_type(node)
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(types.int_type, error.expected)
        assert_equal(types.union(types.int_type, types.none_type), error.actual)


@istest
def can_type_check_generic_function_with_type_parameters():
    signature = nodes.signature(
        type_params=[nodes.formal_type_parameter("T")],
        args=[
            nodes.signature_arg(nodes.ref("T")),
        ],
        returns=nodes.ref("T"),
    )
    args = nodes.arguments([
        nodes.argument("value"),
    ])
    node = nodes.typed(signature, nodes.func("f", args=args, body=[nodes.ret(nodes.ref("value"))]))
    assert_equal(types.func([types.int_type], types.int_type), _infer_func_type(node).instantiate([types.int_type]))


@istest
def can_type_check_generic_function_with_type_parameters_referenced_in_body():
    signature = nodes.signature(
        type_params=[nodes.formal_type_parameter("T")],
        args=[
            nodes.signature_arg(nodes.ref("T")),
        ],
        returns=nodes.ref("T"),
    )
    args = nodes.arguments([
        nodes.argument("value_1"),
    ])
    node = nodes.typed(signature, nodes.func("f", args=args, body=[
        nodes.typed(nodes.ref("T"), nodes.assign([nodes.ref("value_2")], nodes.ref("value_1"))),
        nodes.ret(nodes.ref("value_2")),
    ]))
    assert_equal(types.func([types.int_type], types.int_type), _infer_func_type(node).instantiate([types.int_type]))


@istest
def error_if_name_of_argument_does_not_match_name_in_signature():
    signature = nodes.signature(
        args=[nodes.signature_arg("y", nodes.ref("int"))],
        returns=nodes.ref("int")
    )
    args = nodes.arguments([nodes.argument("x")])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.typed(signature, nodes.func("f", args, body))
    try:
        _infer_func_type(node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_equal("argument 'x' has name 'y' in signature", str(error))
    


@istest
def error_if_type_signature_has_different_number_of_args_from_def():
    signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int")), nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("int")
    )
    args = nodes.arguments([nodes.argument("x")])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.typed(signature, nodes.func("f", args, body))
    try:
        _infer_func_type(node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_equal("args length mismatch: def has 1, signature has 2", str(error))


@istest
def error_if_type_signature_is_missing_from_function_with_args():
    args = nodes.arguments([nodes.argument("x")])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.func("f", args, body)
    try:
        _infer_func_type(node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_equal("signature is missing from function definition", str(error))


@istest
def error_if_type_signature_argument_is_optional_but_def_argument_is_not_optional():
    signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"), optional=True)],
        returns=nodes.type_union([nodes.ref("int"), nodes.ref("none")])
    )
    args = nodes.arguments([nodes.argument("x")])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.typed(signature, nodes.func("f", args, body))
    try:
        _infer_func_type(node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_equal("optional argument 'x' must have default value", str(error))


def _infer_func_type(func_node, type_bindings=None):
    if type_bindings is None:
        type_bindings = {}
    else:
        type_bindings = type_bindings.copy()
    
    type_bindings.update({
        "int": types.meta_type(types.int_type),
        "str": types.meta_type(types.str_type),
        "none": types.meta_type(types.none_type),
        "list": types.meta_type(types.list_type),
    })
    
    context = update_context(func_node, type_bindings=type_bindings)
    return context.lookup(func_node)
