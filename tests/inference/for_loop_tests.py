from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import update_context, ephemeral
from nope.context import bound_context

from .util import assert_statement_is_type_checked


@istest
def for_statement_accepts_iterable_with_iter_method():
    cls = types.scalar_type("Blah")
    cls.attrs.add("__iter__", types.func([], types.iterator(types.str_type)))
    
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [])
    
    context = bound_context({
        "x": None,
        "xs": cls,
    })
    
    update_context(node, context)
    
    assert_equal(types.str_type, context.lookup("x", allow_unbound=True))


@istest
def for_statement_accepts_iterable_with_getitem_method():
    cls = types.scalar_type("Blah")
    cls.attrs.add("__getitem__", types.func([types.int_type], types.str_type))
    
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [])
    
    context = bound_context({
        "x": None,
        "xs": cls,
    })
    
    update_context(node, context)
    
    assert_equal(types.str_type, context.lookup("x", allow_unbound=True))


@istest
def for_statement_requires_iterable_getitem_method_to_accept_integers():
    cls = types.scalar_type("Blah")
    cls.attrs.add("__getitem__", types.func([types.str_type], types.str_type))
    
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    context = bound_context({
        "x": None,
        "xs": cls,
    })
    
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(ref_node, ephemeral.root_node(error.node))
        assert_equal(
            ephemeral.FormalArg(ephemeral.attr(ref_node, "__getitem__"), 0),
            ephemeral.underlying_node(error.node)
        )
        assert_equal(types.int_type, error.expected)
        assert_equal(types.str_type, error.actual)


@istest
def for_statement_has_iterable_type_checked():
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({}))
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def for_statement_requires_iterable_to_have_iter_method():
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({"x": None, "xs": types.int_type}))
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(ref_node, error.node)
        assert_equal("iterable type", error.expected)
        assert_equal(types.int_type, error.actual)


@istest
def iter_method_must_take_no_arguments():
    cls = types.scalar_type("Blah")
    cls.attrs.add("__iter__", types.func([types.str_type], types.iterable(types.str_type)))
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({"x": None, "xs": cls}))
        assert False, "Expected error"
    except errors.BadSignatureError as error:
        assert_equal(ref_node, error.node)


@istest
def iter_method_must_return_iterator():
    cls = types.scalar_type("Blah")
    cls.attrs.add("__iter__", types.func([], types.iterable(types.str_type)))
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.ref("x"), ref_node, [])
    
    try:
        update_context(node, bound_context({"x": None, "xs": cls}))
        assert False, "Expected error"
    except errors.BadSignatureError as error:
        assert_equal(ref_node, error.node)


@istest
def for_statement_target_can_be_supertype_of_iterable_element_type():
    ref_node = nodes.ref("xs")
    node = nodes.for_loop(nodes.subscript(nodes.ref("ys"), nodes.int(0)), ref_node, [])
    
    update_context(node, bound_context({
        "xs": types.list_type(types.int_type),
        "ys": types.list_type(types.object_type),
    }))


@istest
def for_statement_target_cannot_be_strict_subtype_of_iterable_element_type():
    target_sequence_node = nodes.ref("ys")
    target_node = nodes.subscript(target_sequence_node, nodes.int(0))
    iterable_node = nodes.ref("xs")
    node = nodes.for_loop(target_node, iterable_node, [])
    
    try:
        update_context(node, bound_context({
            "xs": types.list_type(types.object_type),
            "ys": types.list_type(types.int_type),
        }))
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(target_sequence_node, ephemeral.root_node(error.node))
        assert_equal(
            ephemeral.FormalArg(ephemeral.attr(target_sequence_node, "__setitem__"), 1),
            ephemeral.underlying_node(error.node)
        )
        assert_equal(types.object_type, error.expected)
        assert_equal(types.int_type, error.actual)


@istest
def for_statement_target_can_be_variable():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [])
    
    # Unassigned case
    update_context(node, bound_context({
        "x": None,
        "xs": types.list_type(types.str_type),
    }))
    # Assigned case
    update_context(node, bound_context({
        "x": types.str_type,
        "xs": types.list_type(types.str_type),
    }))


@istest
def body_of_for_loop_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [
            bad_statement,
        ]),
        bound_context({
            "x": None,
            "xs": types.list_type(types.str_type),
        })
    )


@istest
def else_body_of_for_loop_is_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [], [
            bad_statement
        ]),
        bound_context({
            "x": None,
            "xs": types.list_type(types.str_type),
        })
    )


@istest
def type_of_variable_remains_unbound_if_only_assigned_to_in_for_loop():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [
        nodes.assign("y", nodes.none()),
    ])
    
    context = bound_context({
        "x": None,
        "xs": types.list_type(types.str_type),
        "y": None,
    })
    update_context(node, context)
    assert not context.is_bound("y")
    assert_equal(types.none_type, context.lookup("y", allow_unbound=True))