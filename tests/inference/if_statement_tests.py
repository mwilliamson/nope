from nose.tools import istest, assert_equal

from nope import types, nodes, errors, inference, builtins, name_declaration
from nope.context import Context
from nope.name_resolution import References

from .util import (
    assert_statement_is_type_checked,
    update_context)


@istest
def if_statement_has_condition_type_checked():
    ref_node = nodes.ref("y")
    node = nodes.if_else(ref_node, [], [])
    
    try:
        update_context(node)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(ref_node, error.node)


@istest
def if_statement_has_true_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.if_else(
            nodes.int(1),
            [bad_statement],
            [],
        )
    )


@istest
def if_statement_has_false_body_type_checked():
    assert_statement_is_type_checked(
        lambda bad_statement: nodes.if_else(
            nodes.int(1),
            [],
            [bad_statement],
        )
    )


@istest
def assignment_in_both_branches_of_if_statement_is_added_to_context():
    node = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(1))],
        [nodes.assign("x", nodes.int(2))],
    )
    context = update_context(node, type_bindings={"y": types.object_type})
    assert_equal(types.int_type, context.lookup_name("x"))


@istest
def type_of_variable_is_common_super_type_of_variables_in_both_branches():
    node = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int_literal(42))],
        [nodes.assign("x", nodes.string("blah"))],
    )
    context = update_context(node)
    assert_equal(types.union(types.int_type, types.str_type), context.lookup_name("x"))


@istest
def type_of_variable_is_narrowed_if_reassigned_in_if_body_with_is_none_condition():
    node = nodes.if_else(
        nodes.is_(nodes.ref("x"), nodes.none()),
        [nodes.assign("x", nodes.int_literal(42))],
        [],
    )
    context = update_context(node, type_bindings={
        "x": types.union(types.none_type, types.int_type)
    })
    assert_equal(types.int_type, context.lookup_name("x"))


@istest
def type_of_variable_is_narrowed_if_reassigned_in_if_body_with_is_not_none_condition():
    node = nodes.if_else(
        nodes.bool_not(nodes.is_(nodes.ref("x"), nodes.none())),
        [nodes.assign("x", nodes.string("blah"))],
        [],
    )
    context = update_context(node, type_bindings={
        "x": types.union(types.none_type, types.int_type)
    })
    assert_equal(types.union(types.str_type, types.none_type), context.lookup_name("x"))


@istest
def type_of_variable_is_narrowed_if_reassigned_in_if_body_with_isinstance_condition():
    isinstance_ref = nodes.ref("isinstance")
    variable_in_condition_ref = nodes.ref("x")
    variable_in_assignment_ref = nodes.ref("x")
    str_type_ref = nodes.ref("str")
    variable_declaration = name_declaration.VariableDeclarationNode("x")
    
    node = nodes.if_else(
        nodes.call(isinstance_ref, [variable_in_condition_ref, str_type_ref]),
        [nodes.assign([variable_in_assignment_ref], nodes.int_literal(42))],
        [],
    )
    type_checker = inference._TypeCheckerForModule(
        declaration_finder=None,
        name_resolver=None,
        module_exports=None,
        module_resolver=None,
        module_types=None,
        module=None,
    )
    builtin_declarations = builtins.declarations()
    
    references = References([
        (isinstance_ref, builtin_declarations.declaration("isinstance")),
        (str_type_ref, builtin_declarations.declaration("str")),
        (variable_in_condition_ref, variable_declaration),
        (variable_in_assignment_ref, variable_declaration),
    ])
    context = builtins.module_context(references).enter_func(types.none_type)
    context.update_type(variable_in_condition_ref, types.union(types.str_type, types.none_type))
    type_checker.update_context(node, context)
    assert_equal(types.union(types.int_type, types.none_type), context.lookup_declaration(variable_declaration))
