from nose.tools import istest, assert_equal

from nope import types, nodes, inference, errors
from nope.inference import infer as _infer, update_context
from nope.context import Context, new_module_context


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
def can_infer_type_of_list_of_ints():
    assert_equal(types.list_type(types.int), infer(nodes.list([nodes.int(1), nodes.int(42)])))


@istest
def can_infer_type_of_call():
    context = Context({"f": types.func([types.str], types.int)})
    assert_equal(types.int, infer(nodes.call(nodes.ref("f"), [nodes.str("")]), context))


@istest
def call_arguments_must_match():
    context = Context({"f": types.func([types.str], types.int)})
    arg_node = nodes.int(4)
    node = nodes.call(nodes.ref("f"), [arg_node])
    _assert_type_mismatch(
        lambda: infer(node, context),
        expected=types.str,
        actual=types.int,
        node=arg_node,
    )


@istest
def call_arguments_length_must_match():
    context = Context({"f": types.func([types.str], types.int)})
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
    context = Context({"x": types.str})
    assert_equal(
        types.func([types.str], types.int),
        infer(nodes.attr(nodes.ref("x"), "find"), context)
    )


@istest
def type_error_if_attribute_does_not_exist():
    context = Context({"x": types.str})
    node = nodes.attr(nodes.ref("x"), "swizzlify")
    try:
        infer(node, context)
        assert False, "Expected error"
    except errors.AttributeError as error:
        assert_equal("str object has no attribute swizzlify", str(error))
        assert error.node is node
    

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
    return_node = nodes.ret(nodes.str("!"))
    node = nodes.func(
        "f",
        args=nodes.arguments([]),
        return_annotation=nodes.ref("int"),
        body=[return_node],
    )
    _assert_type_mismatch(lambda: _infer_func_type(node), expected=types.int, actual=types.str, node=return_node)


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
    usage_node = nodes.ref("x")
    node = nodes.func("g", nodes.args([]), None, [
        nodes.expression_statement(nodes.call(nodes.ref("f"), [usage_node])),
        nodes.assign("x", nodes.str("Hello")),
    ])
    
    context = Context({
        "f": types.func([types.str], types.none_type),
        "x": types.int,
    })
    try:
        update_context(node, context)
        assert False, "Expected UnboundLocalError"
    except errors.UnboundLocalError as error:
        assert_equal("local variable x referenced before assignment", str(error))
        assert error.node is usage_node


@istest
def module_exports_are_specified_using_all():
    module_node = nodes.module([
        nodes.assign(["__all__"], nodes.list([nodes.str("x"), nodes.str("z")])),
        nodes.assign(["x"], nodes.str("one")),
        nodes.assign(["y"], nodes.str("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    context = Context({})
    module = inference.check(module_node)
    assert_equal(types.str, module.exports["x"])
    assert_equal(types.int, module.exports["z"])


def _infer_func_type(func_node):
    context = new_module_context()
    update_context(func_node, context)
    return context.lookup(func_node.name)


def _assert_type_mismatch(func, expected, actual, node):
    try:
        func()
        assert False, "Expected type mismatch"
    except errors.TypeMismatchError as mismatch:
        assert_equal(expected, mismatch.expected)
        assert_equal(actual, mismatch.actual)
        assert mismatch.node is node
