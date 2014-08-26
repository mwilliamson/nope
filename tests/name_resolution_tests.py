from nose.tools import istest, assert_is, assert_is_not, assert_equal

from nope import nodes, errors
from nope.name_declaration import VariableDeclarationNode
from nope.name_resolution import resolve, Context
from nope.identity_dict import IdentityDict


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
    context = _new_context(["x"])
    resolve(ref, context)
    
    assert_is(context.definition("x"), context.resolve(ref))


@istest
def error_if_name_is_undefined():
    ref = nodes.ref("x")
    context = _new_context([])
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
def assignment_resolves_names_in_value():
    _assert_children_resolved(
        lambda ref: nodes.assign([nodes.ref("y")], ref),
        other_names=["y"],
    )


@istest
def assignment_resolves_target_name():
    _assert_children_resolved(
        lambda ref: nodes.assign([ref], nodes.none()),
    )


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
def for_loop_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.for_loop(ref, nodes.list([]), [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), ref, [], []),
        other_names=["target"]
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), nodes.list([]), [nodes.expression_statement(ref)], []),
        other_names=["target"]
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), nodes.list([]), [], [nodes.expression_statement(ref)]),
        other_names=["target"]
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
        lambda ref: nodes.try_statement([], handlers=[
            nodes.except_handler(nodes.ref("Exception"), ref, [])
        ]),
        other_names=["Exception"],
    )
    _assert_children_resolved(
        lambda ref: nodes.try_statement([], finally_body=[
            nodes.expression_statement(ref)
        ]),
    )


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
    

@istest
def function_definition_signature_has_names_resolved():
    int_ref = nodes.ref("int")
    str_ref = nodes.ref("str")
    
    signature = nodes.signature(
        args=[nodes.signature_arg(int_ref)],
        returns=str_ref,
    )
    node = nodes.func("f", signature, nodes.arguments([]), [])
    
    context = _new_context(["f", "int", "str"])
    resolve(node, context)
    assert_is(context.definition("int"), context.resolve(int_ref))
    assert_is(context.definition("str"), context.resolve(str_ref))
    

@istest
def function_definitions_adds_function_name_to_context():
    node = nodes.func("f", None, nodes.arguments([]), [])
    
    context = _new_context(["f"])
    resolve(node, context)
    assert_is(context.definition("f"), context.resolve(node))


@istest
def function_definitions_adds_argument_names_to_body_context():
    arg = nodes.argument("x")
    args = nodes.arguments([arg])
    ref = nodes.ref("x")
    body = [nodes.ret(ref)]
    node = nodes.func("f", None, args, body)
    
    context = _new_context(["f"])
    resolve(node, context)
    assert not context.is_defined("x")
    assert_is(context.resolve(arg), context.resolve(ref))


@istest
def function_definitions_bodies_can_access_variables_from_outer_scope():
    args = nodes.arguments([])
    ref = nodes.ref("x")
    body = [nodes.ret(ref)]
    node = nodes.func("f", None, args, body)
    
    context = _new_context(["x", "f"])
    
    resolve(node, context)
    assert_is(context.definition("x"), context.resolve(ref))


@istest
def function_definitions_arguments_shadow_variables_of_same_name_in_outer_scope():
    arg = nodes.argument("x")
    args = nodes.arguments([arg])
    ref = nodes.ref("x")
    body = [nodes.ret(ref)]
    node = nodes.func("f", None, args, body)
    
    context = _new_context(["x", "f"])
    
    resolve(node, context)
    assert_is(context.resolve(arg), context.resolve(ref))
    assert_is_not(context.definition("x"), context.resolve(ref))


@istest
def function_definitions_assignments_shadow_variables_of_same_name_in_outer_scope():
    arg = nodes.argument("x")
    args = nodes.arguments([arg])
    ref = nodes.ref("x")
    body = [nodes.assign([ref], nodes.none())]
    node = nodes.func("f", None, args, body)
    
    context = _new_context(["x", "f"])
    
    resolve(node, context)
    assert_is_not(context.definition("x"), context.resolve(ref))


@istest
def import_multiple_aliases_using_same_name_resolve_to_same_node():
    context = _new_context(["x"])
    first_alias_node = nodes.import_alias("x.y", None)
    second_alias_node = nodes.import_alias("x", None)
    node = nodes.Import([first_alias_node, second_alias_node])
    resolve(node, context)
    assert_is(context.resolve(first_alias_node), context.resolve(second_alias_node))


@istest
def import_from_aliases_are_resolved():
    context = _new_context(["x"])
    alias_node = nodes.import_alias("x", None)
    node = nodes.import_from(["."], [alias_node])
    resolve(node, context)
    assert_equal(context.definition("x"), context.resolve(alias_node))


@istest
def names_in_module_are_defined_and_resolved():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    
    node = nodes.module([
        nodes.assign([target_node], nodes.none()),
        nodes.expression_statement(ref_node),
    ])
    
    context = _new_context(["x"])
    
    resolve(node, context)
    assert_is(context.resolve(ref_node), context.resolve(target_node))
    


def _new_context(names):
    declarations = {}
    for name in names:
        declarations[name] = VariableDeclarationNode(name)
    return Context(declarations, IdentityDict())


def _assert_no_references(node):
    resolve(node, None)


def _assert_children_resolved(create_node, other_names=None):
    if other_names is None:
        other_names = []
    
    context = _new_context(["x"] + other_names)
    
    ref = nodes.ref("x")
    resolve(create_node(ref), context)
    
    assert_is(context.definition("x"), context.resolve(ref))
