from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import infer, ephemeral
from nope.context import bound_context
from .util import assert_type_mismatch


@istest
def can_infer_type_of_call_with_positional_arguments():
    context = bound_context({"f": types.func([types.str_type], types.int_type)})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def can_infer_type_of_call_with_keyword_arguments():
    context = bound_context({
        "f": types.func(
            args=[types.func_arg("name", types.str_type), types.func_arg("hats", types.int_type)],
            return_type=types.boolean_type,
        )
    })
    node = nodes.call(nodes.ref("f"), [], {"name": nodes.string("Bob"), "hats": nodes.int(42)})
    assert_equal(types.boolean_type, infer(node, context))


@istest
def object_can_be_called_if_it_has_call_magic_method():
    cls = types.scalar_type("Blah", [
        types.attr("__call__", types.func([types.str_type], types.int_type)),
    ])
    context = bound_context({"f": cls})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def object_can_be_called_if_it_has_call_magic_method_that_returns_callable():
    second_cls = types.scalar_type("Second", [
        types.attr("__call__", types.func([types.str_type], types.int_type)),
    ])
    first_cls = types.scalar_type("First", [
        types.attr("__call__", second_cls),
    ])
    context = bound_context({"f": first_cls})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def callee_must_be_function_or_have_call_magic_method():
    cls = types.scalar_type("Blah", {})
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
    cls = types.scalar_type("Blah", [types.attr("__call__", types.int_type)])
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
def type_of_positional_arguments_must_match():
    context = bound_context({"f": types.func([types.str_type], types.int_type)})
    arg_node = nodes.int(4)
    node = nodes.call(nodes.ref("f"), [arg_node])
    assert_type_mismatch(
        lambda: infer(node, context),
        expected=types.str_type,
        actual=types.int_type,
        node=arg_node,
    )


@istest
def type_of_keyword_arguments_must_match():
    node = nodes.call(nodes.ref("f"), [], {"name": nodes.string("Bob"), "hats": nodes.int(42)})
    
    context = bound_context({
        "f": types.func(
            args=[types.func_arg("name", types.str_type)],
            return_type=types.boolean_type,
        )
    })
    arg_node = nodes.int(4)
    node = nodes.call(nodes.ref("f"), [], {"name": arg_node})
    assert_type_mismatch(
        lambda: infer(node, context),
        expected=types.str_type,
        actual=types.int_type,
        node=arg_node,
    )


@istest
def error_if_positional_argument_is_missing():
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
def error_if_extra_positional_argument():
    context = bound_context({"f": types.func([], types.int_type)})
    node = nodes.call(nodes.ref("f"), [nodes.string("hello")])
    try:
        infer(node, context)
        assert False, "Expected error"
    except errors.ArgumentsLengthError as error:
        assert_equal(0, error.expected)
        assert_equal(1, error.actual)
        assert error.node is node
