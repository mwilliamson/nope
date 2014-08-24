from nose.tools import istest, assert_is

from nope import nodes
from nope.name_resolution import resolve, Context


@istest
def none_has_no_references():
    _assert_no_references(nodes.none())


@istest
def bool_has_no_references():
    _assert_no_references(nodes.boolean(True))


@istest
def int_has_no_references():
    _assert_no_references(nodes.int(4))


@istest
def str_has_no_references():
    _assert_no_references(nodes.string(""))


@istest
def variable_reference_has_name_resolved():
    definition_node = nodes.ref("x")
    ref = nodes.ref("x")
    context = _new_context()
    context.define("x", definition_node)
    resolve(ref, context)
    
    assert_is(definition_node, context.resolve(ref))


@istest
def list_expression_has_names_in_elements_resolved():
    _assert_children_resolved(
        lambda ref: nodes.list([ref]),
    )


@istest
def call_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.call(ref, []),
    )
    _assert_children_resolved(
        lambda ref: nodes.call(nodes.none(), [ref]),
    )
    _assert_children_resolved(
        lambda ref: nodes.call(nodes.none(), [], {"blah": ref}),
    )


@istest
def attribute_access_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.attr(ref, "blah"),
    )


@istest
def unary_operation_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.neg(ref),
    )


@istest
def binary_operation_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.add(ref, nodes.none()),
    )
    _assert_children_resolved(
        lambda ref: nodes.add(nodes.none(), ref),
    )


@istest
def subscript_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.subscript(ref, nodes.none()),
    )
    _assert_children_resolved(
        lambda ref: nodes.subscript(nodes.none(), ref),
    )


@istest
def assignment_adds_name_to_context():
    context = _new_context()
    definition_node = nodes.ref("x")
    node = nodes.assign([definition_node], nodes.none())
    resolve(node, context)
    assert_is(definition_node, context.definition("x"))


def _new_context():
    return Context()


def _assert_no_references(node):
    resolve(node, None)


def _assert_children_resolved(create_node):
    definition_node = nodes.ref("x")
    ref = nodes.ref("x")
    context = _new_context()
    context.define("x", definition_node)
    resolve(create_node(ref), context)
    
    assert_is(definition_node, context.resolve(ref))
