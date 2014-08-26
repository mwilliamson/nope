from nose.tools import istest, assert_equal, assert_is

from nope import nodes, errors, name_declaration
from nope.name_binding import update_bindings, Context
from nope.identity_dict import IdentityDict


@istest
def variable_is_definitely_bound_after_assignment():
    target_node = nodes.ref("x")
    context = _new_context(IdentityDict([
        (target_node, name_declaration.VariableDeclarationNode("x")),
    ]))
    
    node = nodes.assign([target_node], nodes.none())
    update_bindings(node, context)
    assert_equal(True, context.is_definitely_bound(target_node))


@istest
def value_is_evaluated_before_target_is_bound():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    declaration = name_declaration.VariableDeclarationNode("x")
    context = _new_context(IdentityDict([
        (target_node, declaration),
        (ref_node, declaration),
    ]))
    
    node = nodes.assign([target_node], ref_node)
    try:
        update_bindings(node, context)
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_is(ref_node, error.node)


@istest
def targets_are_evaluated_left_to_right():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    declaration = name_declaration.VariableDeclarationNode("x")
    context = _new_context(IdentityDict([
        (target_node, declaration),
        (ref_node, declaration),
    ]))
    
    node = nodes.assign([nodes.attr(ref_node, "blah"), target_node], nodes.none())
    try:
        update_bindings(node, context)
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_is(ref_node, error.node)


@istest
def error_if_name_is_unbound():
    ref = nodes.ref("x")
    context = _new_context(IdentityDict([
        (ref, name_declaration.VariableDeclarationNode("x")),
    ]))
    
    try:
        update_bindings(ref, context)
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_is(ref, error.node)
        assert_is("x", error.name)


@istest
def no_error_if_name_is_definitely_bound():
    ref = nodes.ref("x")
    target = nodes.ref("x")
    declaration = name_declaration.VariableDeclarationNode("x")
    
    context = _new_context(IdentityDict([
        (ref, declaration),
        (target, declaration),
    ]))
    context.bind(target)
    update_bindings(ref, context)


@istest
def declarations_in_exactly_one_if_else_branch_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda assignment:
        nodes.if_else(nodes.boolean(True), [assignment], [])
    )
    _assert_name_is_not_definitely_bound(lambda assignment:
        nodes.if_else(nodes.boolean(True), [], [assignment])
    )


@istest
def variable_remains_definitely_bound_after_being_reassigned_in_one_branch_of_if_else():
    declaration = name_declaration.VariableDeclarationNode("x")
    target_node = nodes.ref("x")
    context = _new_context(IdentityDict([
        (target_node, declaration)
    ]))
    context.bind(target_node)
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign([target_node], nodes.none())],
        []
    )
    update_bindings(node, context)
    assert context.is_definitely_bound(target_node)


@istest
def declarations_in_both_if_else_branches_are_definitely_bound():
    _assert_name_is_definitely_bound(lambda create_assignment:
        nodes.if_else(nodes.boolean(True), [create_assignment()], [create_assignment()])
    )


@istest
def potentially_bound_variable_becomes_definitely_bound_after_being_assigned_in_both_branches_of_if_else():
    declaration = name_declaration.VariableDeclarationNode("x")
    target_node = nodes.ref("x")
    context = _new_context(IdentityDict([
        (target_node, declaration)
    ]))
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign([target_node], nodes.none())],
        []
    )
    update_bindings(node, context)
    assert not context.is_definitely_bound(target_node)
    
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign([target_node], nodes.none())],
        [nodes.assign([target_node], nodes.none())]
    )
    update_bindings(node, context)
    assert context.is_definitely_bound(target_node)


@istest
def children_of_if_else_are_checked():
    _assert_child_expression_is_checked(lambda ref:
        nodes.if_else(ref, [], [])
    )
    _assert_child_statement_is_checked(lambda ref_statement:
        nodes.if_else(nodes.boolean(True), [ref_statement], [])
    )
    _assert_child_statement_is_checked(lambda ref_statement:
        nodes.if_else(nodes.boolean(True), [], [ref_statement])
    )


@istest
def children_of_while_loop_are_checked():
    _assert_child_expression_is_checked(lambda ref:
        nodes.while_loop(ref, [], [])
    )
    _assert_child_statement_is_checked(lambda ref_statement:
        nodes.while_loop(nodes.boolean(True), [ref_statement], [])
    )
    _assert_child_statement_is_checked(lambda ref_statement:
        nodes.while_loop(nodes.boolean(True), [], [ref_statement])
    )

@istest
def declarations_in_both_body_and_else_body_of_while_loop_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda assignment:
        nodes.while_loop(nodes.boolean(True), [assignment], [assignment])
    )


@istest
def children_of_for_loop_are_checked():
    target_node = nodes.ref("target")
    _assert_child_expression_is_checked(lambda ref:
        nodes.for_loop(nodes.attr(ref, "blah"), nodes.list([]), [], [])
    )
    _assert_child_expression_is_checked(lambda ref:
        nodes.for_loop(target_node, ref, [], []),
        other_refs=[target_node],
    )
    _assert_child_statement_is_checked(lambda ref_statement:
        nodes.for_loop(target_node, nodes.list([]), [ref_statement], []),
        other_refs=[target_node],
    )
    _assert_child_statement_is_checked(lambda ref_statement:
        nodes.for_loop(target_node, nodes.list([]), [], [ref_statement]),
        other_refs=[target_node],
    )

@istest
def for_loop_target_is_defined_but_not_definitely_bound():
    _assert_target_is_not_definitely_bound(lambda target:
        nodes.for_loop(target(), nodes.list([]), [], [])
    )


@istest
def declarations_in_both_body_and_else_body_of_for_loop_are_not_definitely_bound():
    target_node = nodes.ref("target")
    _assert_name_is_not_definitely_bound(lambda assignment:
        nodes.for_loop(target_node, nodes.list([]), [assignment], [assignment]),
        other_refs=[target_node],
    )


@istest
def children_of_try_statement_are_checked():
    _assert_child_statement_is_checked(
        lambda statement_ref: nodes.try_statement([statement_ref]),
    )
    _assert_child_statement_is_checked(
        lambda statement_ref: nodes.try_statement([], handlers=[
            nodes.except_handler(None, None, [statement_ref])
        ]),
    )
    _assert_child_expression_is_checked(
        lambda ref: nodes.try_statement([], handlers=[
            nodes.except_handler(ref, None, [])
        ]),
    )
    _assert_child_expression_is_checked(
        lambda ref: nodes.try_statement([], handlers=[
            nodes.except_handler(nodes.none(), nodes.attr(ref, "blah"), [])
        ]),
    )
    _assert_child_statement_is_checked(
        lambda statement_ref: nodes.try_statement([], finally_body=[
            statement_ref
        ]),
    )


@istest
def declarations_in_body_and_handler_body_and_finally_body_of_try_statement_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda assignment:
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
    _assert_target_is_not_definitely_bound(lambda target:
        nodes.try_statement(
            [],
            handlers=[
                nodes.except_handler(nodes.none(), target(), [])
            ],
        )
    )


@istest
def except_handler_targets_in_same_try_statement_can_share_their_name():
    # TODO: exception handler targets can't be used in nested functions
    _assert_target_is_not_definitely_bound(lambda target:
        nodes.try_statement(
            [],
            handlers=[
                nodes.except_handler(nodes.none(), target(), []),
                nodes.except_handler(nodes.none(), target(), []),
            ],
        )
    )


@istest
def except_handler_targets_cannot_share_their_name_when_nested():
    first_target_node = nodes.ref("error")
    second_target_node = nodes.ref("error")
    
    declaration = name_declaration.ExceptionHandlerTargetNode("error")
    declarations = IdentityDict([
        (first_target_node, declaration),
        (second_target_node, declaration),
    ])
    
    context = _new_context(declarations)
    node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), first_target_node, [
                nodes.try_statement(
                    [],
                    handlers=[
                        nodes.except_handler(nodes.none(), second_target_node, [])
                    ],
                )
            ])
        ],
    )
    try:
        update_bindings(node, context)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal(second_target_node, error.node)
        assert_equal("cannot reuse the same name for nested exception handler targets", str(error))


@istest
def function_name_is_definitely_bound_after_function_definition():
    node = nodes.func("f", None, nodes.arguments([]), [])
    declaration = name_declaration.VariableDeclarationNode("f")
    
    context = _new_context(IdentityDict([(node, declaration)]))
    
    update_bindings(node, context)
    assert_equal(True, context.is_definitely_bound(node))


@istest
def body_of_function_is_checked():
    func_node = nodes.func("f", None, nodes.arguments([]), [])
    
    def create_node(statement_ref):
        func_node.body.append(statement_ref)
        return func_node
    
    _assert_child_statement_is_checked(
        create_node,
        other_refs=[func_node],
    )


@istest
def variables_from_outer_scope_remain_bound():
    ref = nodes.ref("x")
    func_node = nodes.func("f", None, nodes.arguments([]), [nodes.expression_statement(ref)])
    declaration = name_declaration.VariableDeclarationNode("x")
    
    context = _new_context(IdentityDict([
        (func_node, name_declaration.VariableDeclarationNode("f")),
        (ref, declaration),
    ]))
    context.bind(ref)
    
    update_bindings(func_node, context)


@istest
def arguments_of_function_are_definitely_bound():
    arg = nodes.arg("x")
    arg_ref = nodes.ref("x")
    func_node = nodes.func("f", None, nodes.arguments([arg]), [nodes.expression_statement(arg_ref)])
    arg_declaration = name_declaration.VariableDeclarationNode("x")
    
    context = _new_context(IdentityDict([
        (func_node, name_declaration.VariableDeclarationNode("f")),
        (arg, arg_declaration),
        (arg_ref, arg_declaration),
    ]))
    
    update_bindings(func_node, context)


@istest
def exception_handler_targets_cannot_be_accessed_from_nested_function():
    target_node = nodes.ref("error")
    ref_node = nodes.ref("error")
    body = [nodes.ret(ref_node)]
    func_node = nodes.func("f", None, nodes.arguments([]), body)
    try_node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), target_node, [func_node])
        ],
    )
    
    declaration = name_declaration.ExceptionHandlerTargetNode("error")
    declarations = IdentityDict([
        (target_node, declaration),
        (ref_node, declaration),
        (func_node, name_declaration.VariableDeclarationNode("f")),
    ])
    
    context = _new_context(declarations)
    try:
        update_bindings(try_node, context)
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(ref_node, error.node)
        assert_is("error", error.name)


@istest
def import_name_is_definitely_bound_after_import_statement():
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.Import([alias_node])
    declaration = name_declaration.VariableDeclarationNode("x")
    
    context = _new_context(IdentityDict([(alias_node, declaration)]))
    
    update_bindings(node, context)
    assert_equal(True, context.is_definitely_bound(alias_node))


@istest
def import_name_is_definitely_bound_after_import_from_statement():
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.import_from(["."], [alias_node])
    declaration = name_declaration.VariableDeclarationNode("x")
    
    context = _new_context(IdentityDict([(alias_node, declaration)]))
    
    update_bindings(node, context)
    assert_equal(True, context.is_definitely_bound(alias_node))


def _new_context(declarations):
    return Context(declarations, {}, set())


def _assert_name_is_not_definitely_bound(create_node, other_refs=None):
    if other_refs is None:
        other_refs = []
    
    declaration = name_declaration.VariableDeclarationNode("x")
    target_node = nodes.ref("x")
    declarations = IdentityDict([
        (target_node, declaration)
    ])
    
    for other_ref in other_refs:
        declarations[other_ref] = name_declaration.VariableDeclarationNode(other_ref.name)
        
    context = _new_context(declarations)
    
    node = create_node(nodes.assign([target_node], nodes.none()))
    update_bindings(node, context)
    assert not context.is_definitely_bound(target_node)
    

def _assert_name_is_definitely_bound(create_node):
    declaration = name_declaration.VariableDeclarationNode("x")
    ref_node = nodes.ref("x")
    declarations = IdentityDict([(ref_node, declaration)])
    
    def create_assignment():
        target_node = nodes.ref("x")
        declarations[target_node] = declaration
        return nodes.assign([target_node], nodes.none())
    
    node = create_node(create_assignment)
    
    context = _new_context(declarations)
    update_bindings(node, context)
    assert_equal(True, context.is_definitely_bound(ref_node))


def _assert_child_statement_is_checked(create_node, other_refs=None):
    _assert_child_expression_is_checked(
        lambda ref: create_node(nodes.expression_statement(ref)),
        other_refs,
    )


def _assert_child_expression_is_checked(create_node, other_refs=None):
    if other_refs is None:
        other_refs = []
    
    ref = nodes.ref("x")
    declarations = IdentityDict([
        (ref, name_declaration.VariableDeclarationNode("x")),
    ])
    for other_ref in other_refs:
        declarations[other_ref] = name_declaration.VariableDeclarationNode(other_ref.name)
    context = _new_context(declarations)
    
    try:
        update_bindings(create_node(ref), context)
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_is(ref, error.node)
        assert_is("x", error.name)


def _assert_target_is_not_definitely_bound(create_node):
    declaration = name_declaration.VariableDeclarationNode("x")
    target_node = nodes.ref("x")
    declarations = IdentityDict([
        (target_node, declaration)
    ])
    
    def create_target():
        target_node = nodes.ref("x")
        declarations[target_node] = declaration
        return target_node
        
    node = create_node(create_target)
    context = _new_context(declarations)
    update_bindings(node, context)
    assert not context.is_definitely_bound(target_node)
