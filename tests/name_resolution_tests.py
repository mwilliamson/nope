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
def variable_remains_definitely_bound_after_being_reassigned_in_one_branch_of_if_else():
    context = _new_context()
    context.define("x", nodes.ref("x"))
    
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign(nodes.ref("x"), nodes.none())],
        []
    )

    resolve(node, context)

    assert_equal("x", context.definition("x").name)
    assert_equal(True, context.is_definitely_bound("x"))


@istest
def declarations_in_both_if_else_branches_are_defined_and_definitely_bound():
    _assert_assignment_is_defined_and_definitely_bound(lambda create_assignment:
        nodes.if_else(nodes.boolean(True), [create_assignment()], [create_assignment()])
    )


@istest
def potentially_bound_variable_becomes_definitely_bound_after_being_assigned_in_both_branches_of_if_else():
    context = _new_context()
    context.define("x", nodes.ref("x"), is_definitely_bound=False)
    
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign(nodes.ref("x"), nodes.none())],
        [nodes.assign(nodes.ref("x"), nodes.none())]
    )

    resolve(node, context)

    assert_equal("x", context.definition("x").name)
    assert_equal(True, context.is_definitely_bound("x"))


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


@istest
def while_loop_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.while_loop(ref, [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.while_loop(nodes.boolean(True), [nodes.expression_statement(ref)], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.while_loop(nodes.boolean(True), [], [nodes.expression_statement(ref)]),
    )


@istest
def declarations_in_both_body_and_else_body_of_while_loop_are_not_definitely_bound():
    _assert_assignment_is_defined_but_unbound(lambda assignment:
        nodes.while_loop(nodes.boolean(True), [assignment], [assignment])
    )


@istest
def for_loop_target_is_defined_but_not_definitely_bound():
    context = _new_context()
    node = nodes.for_loop(nodes.ref("target"), nodes.list([]), [], [])
    resolve(node, context)
    assert_equal("target", context.definition("target").name)
    assert_equal(False, context.is_definitely_bound("target"))


@istest
def for_loop_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.for_loop(ref, nodes.list([]), [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), ref, [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), nodes.list([]), [nodes.expression_statement(ref)], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), nodes.list([]), [], [nodes.expression_statement(ref)]),
    )


@istest
def declarations_in_both_body_and_else_body_of_for_loop_are_not_definitely_bound():
    _assert_assignment_is_defined_but_unbound(lambda assignment:
        nodes.for_loop(nodes.ref("target"), nodes.list([]), [assignment], [assignment])
    )


@istest
def break_has_no_references():
    _assert_no_references(nodes.break_statement())


@istest
def continue_has_no_references():
    _assert_no_references(nodes.continue_statement())


@istest
def try_statement_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.try_statement([nodes.expression_statement(ref)]),
    )
    _assert_children_resolved(
        lambda ref: nodes.try_statement([], handlers=[
            nodes.except_handler(None, None, [nodes.expression_statement(ref)])
        ]),
    )
    _assert_children_resolved(
        lambda ref: nodes.try_statement([], handlers=[
            nodes.except_handler(ref, None, [])
        ]),
    )
    _assert_children_resolved(
        lambda ref: nodes.try_statement([], finally_body=[
            nodes.expression_statement(ref)
        ]),
    )


@istest
def declarations_in_body_and_handler_body_and_finally_body_of_try_statement_are_not_definitely_bound():
    _assert_assignment_is_defined_but_unbound(lambda assignment:
        nodes.try_statement(
            [assignment],
            handlers=[
                nodes.except_handler(None, None, [assignment])
            ],
            finally_body=[assignment],
        )
    )


@istest
def except_handler_target_is_defined_but_not_definitely_bound():
    context = _new_context()
    node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), nodes.ref("error"), [])
        ],
    )
    resolve(node, context)
    assert_equal("error", context.definition("error").name)
    assert_equal(False, context.is_definitely_bound("error"))


@istest
def except_handler_target_cannot_use_name_that_is_already_defined():
    context = _new_context()
    context.define("error", nodes.ref("error"))
    target_node = nodes.ref("error")
    node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), nodes.ref("error"), [])
        ],
    )
    try:
        resolve(node, context)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal(target_node, error.node)
        assert_equal("exception handler target and variable assignment cannot share the same name", str(error))


@istest
def except_handler_target_cannot_be_later_used_as_ordinary_variable():
    context = _new_context()
    node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), nodes.ref("error"), [])
        ],
    )
    resolve(node, context)
    target_node = nodes.ref("error")
    try:
        resolve(nodes.assign([target_node], nodes.none()), context)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal(target_node, error.node)
        assert_equal("variable assignment and exception handler target cannot share the same name", str(error))


@istest
def name_cannot_be_used_as_variable_assignment_in_one_branch_and_exception_handler_target_in_another():
    context = _new_context()
    target_node = nodes.ref("error")
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign([nodes.ref("error")], nodes.none())],
        [nodes.try_statement(
            [],
            handlers=[
                nodes.except_handler(nodes.none(), target_node, [])
            ],
        )]
    )
    
    try:
        resolve(node, context)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal(target_node, error.node)
        assert_equal("exception handler target and variable assignment cannot share the same name", str(error))


@istest
def raise_statement_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.raise_statement(ref),
    )


@istest
def assert_statement_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.assert_statement(ref),
    )
    _assert_children_resolved(
        lambda ref: nodes.assert_statement(nodes.boolean(False), ref),
    )


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
