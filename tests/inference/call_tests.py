from nose.tools import istest, assert_equal, assert_is

from nope import types, nodes, errors
from nope.inference import ephemeral
from .util import assert_type_mismatch, create_context, infer


@istest
def can_infer_type_of_call_with_positional_arguments():
    context = create_context({"f": types.func([types.str_type], types.int_type)})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def can_infer_type_of_call_with_keyword_arguments():
    context = create_context({
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
    context = create_context({"f": cls})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def object_can_be_called_if_it_has_call_magic_method_that_returns_callable():
    second_cls = types.scalar_type("Second", [
        types.attr("__call__", types.func([types.str_type], types.int_type)),
    ])
    first_cls = types.scalar_type("First", [
        types.attr("__call__", second_cls),
    ])
    context = create_context({"f": first_cls})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), context))


@istest
def callee_must_be_function_or_have_call_magic_method():
    cls = types.scalar_type("Blah", {})
    context = create_context({"f": cls})
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
    context = create_context({"f": cls})
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
    context = create_context({"f": types.func([types.str_type], types.int_type)})
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
    
    context = create_context({
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
    node = _create_call([])
    try:
        _infer_function_call(types.func([types.str_type], types.int_type), node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_is(node, error.node)
        assert_equal("missing 1st positional argument", str(error))


@istest
def if_positional_has_name_then_that_name_is_used_in_missing_argument_message():
    node = _create_call([])
    try:
        _infer_function_call(types.func([types.func_arg("message", types.str_type)], types.int_type), node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_is(node, error.node)
        assert_equal("missing argument 'message'", str(error))


@istest
def error_if_extra_positional_argument():
    node = _create_call([nodes.string("hello")])
    try:
        _infer_function_call(types.func([], types.int_type), node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_is(node, error.node)
        assert_equal("function takes 0 positional arguments but 1 was given", str(error))


@istest
def error_if_extra_keyword_argument():
    node = _create_call([], {"message": nodes.string("hello")})
    try:
        _infer_function_call(types.func([], types.int_type), node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_is(node, error.node)
        assert_equal("unexpected keyword argument 'message'", str(error))


@istest
def error_if_argument_is_passed_both_by_position_and_keyword():
    node = _create_call([nodes.string("Jim")], {"name": nodes.string("Bob")})
    
    func_type = types.func(
        args=[types.func_arg("name", types.str_type)],
        return_type=types.boolean_type,
    )
    try:
        _infer_function_call(func_type, node)
        assert False, "Expected error"
    except errors.ArgumentsError as error:
        assert_is(node, error.node)
        assert_equal("multiple values for argument 'name'", str(error))


def _infer_function_call(func_type, call_node):
    context = create_context({"f": func_type})
    return infer(call_node, context)


def _create_call(args, kwargs=None):
    return nodes.call(nodes.ref("f"), args, kwargs)
