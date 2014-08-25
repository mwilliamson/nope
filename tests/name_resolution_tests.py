from nose.tools import istest, assert_is, assert_equal

from nope import nodes, errors
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
    declaration = context.define("x", definition_node)
    resolve(ref, context)
    
    assert_is(declaration, context.resolve(ref))


@istest
def error_if_name_is_undefined():
    ref = nodes.ref("x")
    context = _new_context()
    try:
        resolve(ref, context)
        assert False, "Expected error"
    except errors.UndefinedNameError as error:
        assert_is(ref, error.node)
        assert_is("x", error.name)


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
def return_statement_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.ret(ref),
    )
    _assert_no_references(nodes.ret(None))


@istest
def expression_statement_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.expression_statement(ref),
    )


@istest
def assignment_adds_definition_to_context():
    context = _new_context()
    definition_node = nodes.ref("x")
    node = nodes.assign([definition_node], nodes.none())
    resolve(node, context)
    assert_equal("x", context.definition("x").name)
    assert_equal(True, context.is_definitely_bound("x"))


@istest
def assignment_resolves_names_in_value():
    _assert_children_resolved(
        lambda ref: nodes.assign([nodes.ref("y")], ref),
    )


@istest
def assignment_resolves_target_names_when_variable_is_already_defined():
    _assert_children_resolved(
        lambda ref: nodes.assign([ref], nodes.none()),
    )


@istest
def assignment_resolves_target_names_when_variable_is_not_yet_defined():
    context = _new_context()
    definition_node = nodes.ref("x")
    node = nodes.assign([definition_node], nodes.none())
    resolve(node, context)
    assert_is(context.definition("x"), context.resolve(definition_node))


@istest
def if_else_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.if_else(ref, [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.if_else(nodes.boolean(True), [nodes.expression_statement(ref)], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.if_else(nodes.boolean(True), [], [nodes.expression_statement(ref)]),
    )


@istest
def declarations_in_exactly_one_if_else_branch_are_defined_but_not_definitely_bound():
    _assert_assignment_is_defined_but_unbound(lambda assignment:
        nodes.if_else(nodes.boolean(True), [assignment], [])
    )
    _assert_assignment_is_defined_but_unbound(lambda assignment:
        nodes.if_else(nodes.boolean(True), [], [assignment])
    )


@istest
def declarations_in_both_if_else_branches_are_defined_and_definitely_bound():
    _assert_assignment_is_defined_and_definitely_bound(lambda create_assignment:
        nodes.if_else(nodes.boolean(True), [create_assignment()], [create_assignment()])
    )


@istest
def referred_declaration_in_branch_is_same_as_declaration_outside_of_branch():
    context = _new_context()
    ref_node = nodes.ref("x")
    node = nodes.if_else(
        nodes.boolean(True),
        [
            nodes.assign([nodes.ref("x")], nodes.none()),
            ref_node,
        ],
        []
    )
    resolve(node, context)
    assert_is(context.definition("x"), context.resolve(ref_node))


def _new_context():
    return Context({}, {}, {})


def _assert_no_references(node):
    resolve(node, None)


def _assert_children_resolved(create_node):
    ref = nodes.ref("x")
    context = _new_context()
    declaration = context.define("x", nodes.ref("x"))
    resolve(create_node(ref), context)
    
    assert_is(declaration, context.resolve(ref))


def _assert_assignment_is_defined_but_unbound(create_node):
    context = _new_context()
    node = create_node(nodes.assign([nodes.ref("x")], nodes.none()))
    resolve(node, context)
    assert_equal("x", context.definition("x").name)
    assert_equal(False, context.is_definitely_bound("x"))
    

def _assert_assignment_is_defined_and_definitely_bound(create_node):
    def create_assignment():
        return nodes.assign([nodes.ref("x")], nodes.none())
    
    context = _new_context()
    node = create_node(create_assignment)
    resolve(node, context)
    assert_equal("x", context.definition("x").name)
    assert_equal(True, context.is_definitely_bound("x"))
