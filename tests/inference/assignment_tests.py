from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import ephemeral
from .util import update_context


@istest
def assignment_sets_type_of_target_variable_to_type_of_value():
    node = nodes.assign([nodes.ref("x")], nodes.int_literal(1))
    context = update_context(node)
    assert_equal(types.int_type, context.lookup_name("x"))


@istest
def assignment_to_list_allows_subtype():
    node = nodes.assign([nodes.subscript(nodes.ref("x"), nodes.int_literal(0))], nodes.str_literal("Hello"))
    type_bindings = {"x": types.list_type(types.object_type)}
    update_context(node, type_bindings=type_bindings)


@istest
def assignment_to_list_does_not_allow_supertype():
    target_sequence_node = nodes.ref("x")
    value_node = nodes.ref("y")
    node = nodes.assign([nodes.subscript(target_sequence_node, nodes.int_literal(0))], value_node)
    type_bindings = {
        "x": types.list_type(types.str_type),
        "y": types.object_type,
    }
    try:
        update_context(node, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnexpectedTargetTypeError as error:
        assert_equal(target_sequence_node, ephemeral.root_node(error.node))
        assert_equal(
            ephemeral.FormalArg(ephemeral.attr(target_sequence_node, "__setitem__"), 1),
            ephemeral.underlying_node(error.node)
        )
        assert_equal(types.object_type, error.value_type)
        assert_equal(types.str_type, error.target_type)


@istest
def assignment_to_attribute_allows_subtype():
    cls = types.scalar_type("X", [types.attr("y", types.object_type, read_only=False)])
    
    node = nodes.assign([nodes.attr(nodes.ref("x"), "y")], nodes.str_literal("Hello"))
    type_bindings = {"x": cls}
    update_context(node, type_bindings=type_bindings)


@istest
def assignment_to_attribute_does_not_allow_strict_supertype():
    cls = types.scalar_type("X", [types.attr("y", types.str_type, read_only=True)])
    
    attr_node = nodes.attr(nodes.ref("x"), "y")
    node = nodes.assign([attr_node], nodes.ref("obj"))
    type_bindings = {"x": cls, "obj": types.object_type}
    try:
        update_context(node, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnexpectedTargetTypeError as error:
        assert_equal(attr_node, error.node)
        assert_equal(types.object_type, error.value_type)
        assert_equal(types.str_type, error.target_type)



@istest
def assignment_to_tuple_unpacks_tuple_type():
    node = nodes.assign(
        [nodes.tuple_literal([nodes.ref("x"), nodes.ref("y")])],
        nodes.ref("value")
    )
    context = update_context(node, type_bindings={
        "value": types.tuple_type(types.int_type, types.str_type),
    })
    assert_equal(types.int_type, context.lookup_name("x"))
    assert_equal(types.str_type, context.lookup_name("y"))



@istest
def assignment_to_tuple_must_have_correct_length_tuple():
    tuple_node = nodes.tuple_literal([nodes.ref("x"), nodes.ref("y")])
    node = nodes.assign(
        [tuple_node],
        nodes.ref("value")
    )
    try:
        update_context(node, type_bindings={
            "value": types.tuple_type(types.int_type),
        })
        assert False, "Expected error"
    except errors.UnpackError as error:
        assert_equal(tuple_node, error.node)
        assert_equal("need 2 values to unpack, but only have 1" , str(error))



@istest
def assignment_to_tuple_must_have_tuple_value():
    tuple_node = nodes.tuple_literal([nodes.ref("x")])
    node = nodes.assign(
        [tuple_node],
        nodes.ref("value")
    )
    try:
        update_context(node, type_bindings={
            "value": types.list_type(types.int_type),
        })
        assert False, "Expected error"
    except errors.CanOnlyUnpackTuplesError as error:
        assert_equal(tuple_node, error.node)
        assert_equal("only tuples can be unpacked" , str(error))


@istest
def cannot_reassign_read_only_attribute():
    cls = types.scalar_type("X", [types.attr("y", types.str_type, read_only=True)])
    
    attr_node = nodes.attr(nodes.ref("x"), "y")
    node = nodes.assign([attr_node], nodes.str_literal("Hello"))
    type_bindings = {"x": cls}
    try:
        update_context(node, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.ReadOnlyAttributeError as error:
        assert_equal(attr_node, error.node)
        assert_equal("'X' attribute 'y' is read-only", str(error))


@istest
def variables_can_change_type():
    node = nodes.assign(["x"], nodes.int_literal(1))
    type_bindings = {"x": types.none_type}
    context = update_context(node, type_bindings=type_bindings)
    assert_equal(types.int_type, context.lookup_name("x"))


@istest
def when_target_already_has_type_that_type_is_used_as_type_hint():
    node = nodes.assign([nodes.ref("x")], nodes.list_literal([nodes.str_literal("Hello")]))
    type_bindings = {"x": types.list_type(types.object_type)}
    context = update_context(node, type_bindings=type_bindings)
    assert_equal(types.list_type(types.object_type), context.lookup_name("x"))


@istest
def when_target_has_explicit_type_that_type_is_used_as_type_hint():
    node = nodes.assign(
        [nodes.ref("x")],
        nodes.list_literal([nodes.str_literal("Hello")]),
        explicit_type=nodes.type_apply(nodes.ref("list"), [nodes.ref("object")])
    )
    context = update_context(node, type_bindings={
        "list": types.meta_type(types.list_type),
        "object": types.meta_type(types.object_type),
    })
    assert_equal(types.list_type(types.object_type), context.lookup_name("x"))


@istest
def given_explicit_type_when_value_does_not_have_that_type_an_error_is_raised():
    value_node = nodes.none()
    node = nodes.assign(
        [nodes.ref("x")],
        value_node,
        explicit_type=nodes.ref("int")
    )
    try:
        update_context(node, type_bindings={
            "int": types.meta_type(types.int_type),
        })
        assert False, "Expected error"
    except errors.UnexpectedValueTypeError as error:
        assert_equal(value_node, error.node)
        assert_equal(types.none_type, error.actual)
        assert_equal(types.int_type, error.expected)
