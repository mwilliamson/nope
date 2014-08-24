from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import update_context, ephemeral
from nope.context import bound_context, Context, Variable, Boundness


@istest
def assignment_adds_variable_to_context():
    node = nodes.assign(["x"], nodes.int(1))
    context = bound_context({"x": None})
    update_context(node, context)
    assert_equal(types.int_type, context.lookup("x"))


@istest
def assignment_to_list_allows_subtype():
    node = nodes.assign([nodes.subscript(nodes.ref("x"), nodes.int(0))], nodes.string("Hello"))
    context = bound_context({"x": types.list_type(types.object_type)})
    update_context(node, context)


@istest
def assignment_to_list_does_not_allow_supertype():
    target_sequence_node = nodes.ref("x")
    value_node = nodes.ref("y")
    node = nodes.assign([nodes.subscript(target_sequence_node, nodes.int(0))], value_node)
    context = bound_context({
        "x": types.list_type(types.str_type),
        "y": types.object_type,
    })
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(target_sequence_node, ephemeral.root_node(error.node))
        assert_equal(
            ephemeral.FormalArg(ephemeral.attr(target_sequence_node, "__setitem__"), 1),
            ephemeral.underlying_node(error.node)
        )
        assert_equal(types.object_type, error.expected)
        assert_equal(types.str_type, error.actual)


@istest
def assignment_to_attribute_allows_subtype():
    cls = types.scalar_type("X", [types.attr("y", types.object_type)])
    
    node = nodes.assign([nodes.attr(nodes.ref("x"), "y")], nodes.string("Hello"))
    context = bound_context({"x": cls})
    update_context(node, context)


@istest
def assignment_to_attribute_does_not_allow_strict_supertype():
    cls = types.scalar_type("X", [types.attr("y", types.str_type)])
    
    attr_node = nodes.attr(nodes.ref("x"), "y")
    node = nodes.assign([attr_node], nodes.ref("obj"))
    context = bound_context({"x": cls, "obj": types.object_type})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.BadAssignmentError as error:
        assert_equal(attr_node, error.node)
        assert_equal(types.object_type, error.value_type)
        assert_equal(types.str_type, error.target_type)


@istest
def cannot_reassign_read_only_attribute():
    cls = types.scalar_type("X", [types.attr("y", types.str_type, read_only=True)])
    
    attr_node = nodes.attr(nodes.ref("x"), "y")
    node = nodes.assign([attr_node], nodes.string("Hello"))
    context = bound_context({"x": cls})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.ReadOnlyAttributeError as error:
        assert_equal(attr_node, error.node)
        assert_equal("'X' attribute 'y' is read-only", str(error))


@istest
def variables_cannot_change_type():
    node = nodes.assign(["x"], nodes.int(1))
    context = bound_context({"x": types.none_type})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.BadAssignmentError as error:
        assert_equal(node, error.node)


@istest
def variables_cannot_change_type_even_if_variable_is_potentially_unbound():
    node = nodes.assign(["x"], nodes.int(1))
    context = Context({"x": Variable(types.none_type, boundness=Boundness.maybe)})
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.BadAssignmentError as error:
        assert_equal(node, error.node)


@istest
def variables_can_be_reassigned_if_type_is_consistent():
    node = nodes.assign(["x"], nodes.int(1))
    context = bound_context({"x": types.object_type})
    update_context(node, context)
    assert_equal(types.object_type, context.lookup("x"))


@istest
def variables_are_shadowed_in_defs():
    node = nodes.func("g", nodes.signature(), nodes.args([]), [
        nodes.assign(["x"], nodes.string("Hello")),
        nodes.expression_statement(nodes.call(nodes.ref("f"), [nodes.ref("x")])),
    ])
    
    context = bound_context({
        "g": None,
        "f": types.func([types.str_type], types.none_type),
        "x": types.int_type,
    })
    update_context(node, context)
    
    assert_equal(types.int_type, context.lookup("x"))


@istest
def local_variables_cannot_be_used_before_assigned():
    usage_node = nodes.ref("x")
    node = nodes.func("g", nodes.signature(), nodes.args([]), [
        nodes.expression_statement(nodes.call(nodes.ref("f"), [usage_node])),
        nodes.assign("x", nodes.string("Hello")),
    ])
    
    context = bound_context({
        "f": types.func([types.str_type], types.none_type),
        "x": types.int_type,
    })
    try:
        update_context(node, context)
        assert False, "Expected UnboundLocalError"
    except errors.UnboundLocalError as error:
        assert_equal("local variable x referenced before assignment", str(error))
        assert error.node is usage_node
