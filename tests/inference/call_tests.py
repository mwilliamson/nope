from nose.tools import istest, assert_equal, assert_is

from nope import types, nodes, errors
from nope.inference import ephemeral
from .util import assert_type_mismatch, infer


@istest
def can_infer_type_of_call_with_positional_arguments():
    type_bindings = {"f": types.func([types.str_type], types.int_type)}
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), type_bindings=type_bindings))


@istest
def can_infer_type_of_call_with_keyword_arguments():
    type_bindings = {
        "f": types.func(
            args=[types.func_arg("name", types.str_type), types.func_arg("hats", types.int_type)],
            return_type=types.boolean_type,
        )
    }
    node = nodes.call(nodes.ref("f"), [], {"name": nodes.string("Bob"), "hats": nodes.int(42)})
    assert_equal(types.boolean_type, infer(node, type_bindings=type_bindings))


@istest
def object_can_be_called_if_it_has_call_magic_method():
    cls = types.scalar_type("Blah", [
        types.attr("__call__", types.func([types.str_type], types.int_type)),
    ])
    type_bindings = {"f": cls}
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), type_bindings=type_bindings))


@istest
def object_can_be_called_if_it_has_call_magic_method_that_returns_callable():
    second_cls = types.scalar_type("Second", [
        types.attr("__call__", types.func([types.str_type], types.int_type)),
    ])
    first_cls = types.scalar_type("First", [
        types.attr("__call__", second_cls),
    ])
    type_bindings = {"f": first_cls}
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.string("")]), type_bindings=type_bindings))


@istest
def callee_can_be_overloaded_func_type_where_choice_is_unambiguous_given_args():
    type_bindings = {"f": types.overloaded_func(
        types.func([types.str_type], types.int_type),
        types.func([types.int_type], types.str_type),
    )}
    node = nodes.call(nodes.ref("f"), [nodes.string("")])
    assert_equal(types.int_type, infer(node, type_bindings=type_bindings))


@istest
def return_type_is_common_super_type_of_possible_return_types_of_overloaded_function():
    type_bindings = {"f": types.overloaded_func(
        types.func([types.object_type], types.int_type),
        types.func([types.str_type], types.str_type),
    )}
    node = nodes.call(nodes.ref("f"), [nodes.string("")])
    assert_equal(
        types.common_super_type([types.int_type, types.str_type]),
        infer(node, type_bindings=type_bindings)
    )


@istest
def callee_must_be_function_or_have_call_magic_method():
    cls = types.scalar_type("Blah", {})
    type_bindings = {"f": cls}
    callee_node = nodes.ref("f")
    try:
        infer(nodes.call(callee_node, []), type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(callee_node, error.node)
        assert_equal("callable object", error.expected)
        assert_equal(cls, error.actual)


@istest
def call_attribute_must_be_function():
    cls = types.scalar_type("Blah", [types.attr("__call__", types.int_type)])
    type_bindings = {"f": cls}
    callee_node = nodes.ref("f")
    try:
        infer(nodes.call(callee_node, []), type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(callee_node, ephemeral.root_node(error.node))
        assert_equal("callable object", error.expected)
        assert_equal(types.int_type, error.actual)


@istest
def type_of_positional_arguments_must_match():
    type_bindings = {"f": types.func([types.str_type], types.int_type)}
    arg_node = nodes.int(4)
    node = nodes.call(nodes.ref("f"), [arg_node])
    assert_type_mismatch(
        lambda: infer(node, type_bindings=type_bindings),
        expected=types.str_type,
        actual=types.int_type,
        node=arg_node,
    )


@istest
def type_of_keyword_arguments_must_match():
    node = nodes.call(nodes.ref("f"), [], {"name": nodes.string("Bob"), "hats": nodes.int(42)})
    
    type_bindings = {
        "f": types.func(
            args=[types.func_arg("name", types.str_type)],
            return_type=types.boolean_type,
        )
    }
    arg_node = nodes.int(4)
    node = nodes.call(nodes.ref("f"), [], {"name": arg_node})
    assert_type_mismatch(
        lambda: infer(node, type_bindings=type_bindings),
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
    return infer(call_node, type_bindings={"f": func_type})


def _create_call(args, kwargs=None):
    return nodes.call(nodes.ref("f"), args, kwargs)
