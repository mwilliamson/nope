from nose.tools import istest, assert_equal, assert_is

from nope import nodes, errors, name_declaration, types
from nope.name_binding import check_bindings
from nope.name_resolution import References
from nope.identity_dict import IdentityDict
from nope.types import TypeLookup
from .inference.util import context_manager_class


@istest
def children_of_list_comprehension_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.list_comprehension(
            generate.unbound_ref(),
            nodes.comprehension(
                generate.bound_ref("x", types.int_type),
                nodes.list_literal([]),
            ),
        )
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.list_comprehension(
            nodes.none(),
            nodes.comprehension(
                nodes.attr(generate.unbound_ref(), "x"),
                nodes.list_literal([]),
            ),
        )
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.list_comprehension(
            nodes.none(),
            nodes.comprehension(
                generate.bound_ref("x", types.int_type),
                generate.unbound_ref(),
            ),
        )
    )


@istest
def list_comprehension_target_is_definitely_bound():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    node = nodes.list_comprehension(
        ref_node,
        nodes.comprehension(
            target_node,
            nodes.list_literal([]),
        ),
    )
    
    declaration = name_declaration.VariableDeclarationNode("x")
    
    references = References([
        (ref_node, declaration),
        (target_node, declaration),
    ])
    
    _updated_bindings(node, references)


@istest
def variable_is_definitely_bound_after_assignment():
    target_node = nodes.ref("x")
    node = nodes.assign([target_node], nodes.none())
    
    references = References([
        (target_node, name_declaration.VariableDeclarationNode("x")),
    ])
    
    bindings = _updated_bindings(node, references)
    assert_equal(True, bindings.is_definitely_bound(target_node))


@istest
def value_is_evaluated_before_target_is_bound():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    node = nodes.assign([target_node], ref_node)
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([
        (target_node, declaration),
        (ref_node, declaration),
    ])
    
    _assert_is_unbound_error(ref_node, lambda: _updated_bindings(node, references))


@istest
def targets_are_evaluated_left_to_right():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    node = nodes.assign([nodes.attr(ref_node, "blah"), target_node], nodes.none())
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([
        (target_node, declaration),
        (ref_node, declaration),
    ])
    
    _assert_is_unbound_error(ref_node, lambda: _updated_bindings(node, references))


@istest
def variable_in_tuple_is_definitely_bound_after_assignment():
    target_node = nodes.ref("x")
    node = nodes.assign([nodes.tuple_literal([target_node])], nodes.tuple_literal([nodes.none()]))
    
    references = References([
        (target_node, name_declaration.VariableDeclarationNode("x")),
    ])
    
    bindings = _updated_bindings(node, references)
    assert_equal(True, bindings.is_definitely_bound(target_node))


@istest
def error_if_name_is_unbound():
    ref = nodes.ref("x")
    references = References([
        (ref, name_declaration.VariableDeclarationNode("x")),
    ])
    
    _assert_is_unbound_error(ref, lambda: _updated_bindings(ref, references))


@istest
def no_error_if_name_is_definitely_bound():
    ref = nodes.ref("x")
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([
        (ref, declaration),
    ])
    
    _updated_bindings(ref, references, is_definitely_bound={declaration: True})


@istest
def declarations_in_exactly_one_if_else_branch_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.if_else(nodes.boolean(True), [generate.assignment()], [])
    )
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.if_else(nodes.boolean(True), [], [generate.assignment()])
    )


@istest
def variable_remains_definitely_bound_after_being_reassigned_in_one_branch_of_if_else():
    target_node = nodes.ref("x")
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign([target_node], nodes.none())],
        []
    )
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([
        (target_node, declaration)
    ])
    
    bindings = _updated_bindings(node, references, is_definitely_bound={declaration: True})
    assert bindings.is_definitely_bound(target_node)


@istest
def declarations_in_both_if_else_branches_are_definitely_bound():
    _assert_name_is_definitely_bound(lambda generate:
        nodes.if_else(nodes.boolean(True), [generate.assignment()], [generate.assignment()])
    )


@istest
def potentially_bound_variable_becomes_definitely_bound_after_being_assigned_in_both_branches_of_if_else():
    target_node = nodes.ref("x")
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign([target_node], nodes.none())],
        []
    )
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([
        (target_node, declaration)
    ])
    bindings = _updated_bindings(node, references)
    assert not bindings.is_definitely_bound(target_node)
    
    node = nodes.if_else(
        nodes.boolean(True),
        [nodes.assign([target_node], nodes.none())],
        [nodes.assign([target_node], nodes.none())]
    )
    bindings = _updated_bindings(node, references)
    assert bindings.is_definitely_bound(target_node)


@istest
def children_of_if_else_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.if_else(
            generate.unbound_ref(),
            [],
            []
        )
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.if_else(
            nodes.boolean(True),
            [generate.unbound_ref_statement()],
            []
        )
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.if_else(
            nodes.boolean(True),
            [],
            [generate.unbound_ref_statement()]
        )
    )


@istest
def children_of_while_loop_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.while_loop(generate.unbound_ref(), [], [])
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.while_loop(
            nodes.boolean(True),
            [generate.unbound_ref_statement()],
            []
        )
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.while_loop(
            nodes.boolean(True),
            [],
            [generate.unbound_ref_statement()]
        )
    )

@istest
def declarations_in_both_body_and_else_body_of_while_loop_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.while_loop(nodes.boolean(True), [generate.assignment()], [generate.assignment()])
    )


@istest
def children_of_for_loop_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.for_loop(
            nodes.attr(generate.unbound_ref(), "blah"),
            nodes.list_literal([]),
            [],
            []
        )
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.for_loop(
            generate.target(),
            generate.unbound_ref(),
            [],
            []
        ),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.for_loop(
            generate.target(),
            nodes.list_literal([]),
            [generate.unbound_ref_statement()],
            []
        ),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.for_loop(
            generate.target(),
            nodes.list_literal([]),
            [],
            [generate.unbound_ref_statement()],
        ),
    )

@istest
def for_loop_target_is_defined_but_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.for_loop(generate.target(), nodes.list_literal([]), [], [])
    )


@istest
def declarations_in_both_body_and_else_body_of_for_loop_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.for_loop(
            generate.target(),
            nodes.list_literal([]),
            [generate.assignment()],
            [generate.assignment()]
        ),
    )


@istest
def children_of_try_statement_are_checked():
    _assert_child_statement_is_checked(lambda generate:
        nodes.try_statement([generate.unbound_ref_statement()]),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.try_statement([], handlers=[
            nodes.except_handler(None, None, [generate.unbound_ref_statement()])
        ]),
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.try_statement([], handlers=[
            nodes.except_handler(generate.unbound_ref(), None, [])
        ]),
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.try_statement([], handlers=[
            nodes.except_handler(nodes.none(), nodes.attr(generate.unbound_ref(), "blah"), [])
        ]),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.try_statement([], finally_body=[
            generate.unbound_ref_statement()
        ]),
    )


@istest
def declarations_in_body_and_handler_body_and_finally_body_of_try_statement_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.try_statement(
            [generate.assignment()],
            handlers=[
                nodes.except_handler(None, None, [generate.assignment()])
            ],
            finally_body=[generate.assignment()],
        )
    )


@istest
def except_handler_target_is_defined_but_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.try_statement(
            [],
            handlers=[
                nodes.except_handler(nodes.none(), generate.target(), [])
            ],
        )
    )


@istest
def except_handler_targets_in_same_try_statement_can_share_their_name():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.try_statement(
            [],
            handlers=[
                nodes.except_handler(nodes.none(), generate.target(), []),
                nodes.except_handler(nodes.none(), generate.target(), []),
            ],
        )
    )


@istest
def except_handler_targets_cannot_share_their_name_when_nested():
    first_target_node = nodes.ref("error")
    second_target_node = nodes.ref("error")
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
    
    declaration = name_declaration.ExceptionHandlerTargetNode("error")
    references = References([
        (first_target_node, declaration),
        (second_target_node, declaration),
    ])
    
    try:
        _updated_bindings(node, references)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal(second_target_node, error.node)
        assert_equal("cannot reuse the same name for nested exception handler targets", str(error))


@istest
def children_of_with_statement_are_checked():
    context_manager_type = context_manager_class(exit_type=types.none_type)
    
    _assert_child_expression_is_checked(lambda generate:
        nodes.with_statement(
            generate.unbound_ref(),
            None,
            []
        ),
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.with_statement(
            generate.bound_ref("manager", context_manager_type),
            nodes.attr(generate.unbound_ref(), "blah"),
            []
        ),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.with_statement(
            generate.bound_ref("manager", context_manager_type),
            None,
            [generate.unbound_ref_statement()]
        ),
    )


@istest
def with_statement_target_is_definitely_bound_in_body():
    manager_ref = nodes.ref("manager")
    target_ref = nodes.ref("target")
    var_ref = nodes.ref("target")
    statement = nodes.with_statement(manager_ref, target_ref, [nodes.expression_statement(var_ref)])
    
    manager_declaration = name_declaration.VariableDeclarationNode("manager")
    target_declaration = name_declaration.VariableDeclarationNode("target")
    references = References([
        (manager_ref, manager_declaration),
        (target_ref, target_declaration),
        (var_ref, target_declaration),
    ])
    
    _updated_bindings(
        statement,
        references,
        is_definitely_bound={manager_declaration: True},
        type_lookup=TypeLookup(IdentityDict([(manager_ref, context_manager_class(exit_type=types.none_type))]))
    )


@istest
def assigned_variables_in_with_statement_body_are_still_bound_after_exit_if_exit_method_always_returns_none():
    context_manager_type = context_manager_class(exit_type=types.none_type)
    _assert_name_is_definitely_bound(lambda generate:
        nodes.with_statement(
            generate.bound_ref("manager", context_manager_type),
            None,
            [generate.assignment()]
        ),
    )


@istest
def assigned_variables_in_with_statement_body_are_unbound_after_exit_if_exit_method_does_not_return_none():
    context_manager_type = context_manager_class(exit_type=types.bool_type)
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.with_statement(
            generate.bound_ref("manager", context_manager_type),
            None,
            [generate.assignment()]
        ),
    )


@istest
def function_name_is_definitely_bound_after_function_definition():
    node = nodes.func("f", nodes.arguments([]), [])
    declaration = name_declaration.VariableDeclarationNode("f")
    
    references = References([(node, declaration)])
    
    bindings = _updated_bindings(node, references)
    assert_equal(True, bindings.is_definitely_bound(node))


@istest
def body_of_function_is_checked():
    _assert_child_statement_is_checked(lambda generate:
        generate.func("f", nodes.arguments([]), [generate.unbound_ref_statement()])
    )


@istest
def variables_from_outer_scope_remain_bound():
    ref = nodes.ref("x")
    func_node = nodes.func("f", nodes.arguments([]), [nodes.expression_statement(ref)])
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([
        (func_node, name_declaration.VariableDeclarationNode("f")),
        (ref, declaration),
    ])
    
    _updated_bindings(func_node, references, is_definitely_bound={declaration: True})


@istest
def arguments_of_function_are_definitely_bound():
    arg = nodes.arg("x")
    arg_ref = nodes.ref("x")
    func_node = nodes.func("f", nodes.arguments([arg]), [nodes.expression_statement(arg_ref)])
    
    arg_declaration = name_declaration.VariableDeclarationNode("x")
    
    references = References([
        (func_node, name_declaration.VariableDeclarationNode("f")),
        (arg, arg_declaration),
        (arg_ref, arg_declaration),
    ])
    
    _updated_bindings(func_node, references)


@istest
def type_parameters_of_function_are_definitely_bound():
    param = nodes.formal_type_parameter("T")
    arg_ref = nodes.ref("T")
    returns_ref = nodes.ref("T")
    func_node = nodes.typed(
        nodes.signature(type_params=[param], args=[nodes.signature_arg(arg_ref)], returns=returns_ref),
        nodes.func("f", nodes.arguments([]), []),
    )
    
    param_declaration = name_declaration.VariableDeclarationNode("T")
    
    references = References([
        (func_node, name_declaration.VariableDeclarationNode("f")),
        (param, param_declaration),
        (arg_ref, param_declaration),
        (returns_ref, param_declaration),
    ])
    
    _updated_bindings(func_node, references)


@istest
def exception_handler_targets_cannot_be_accessed_from_nested_function():
    target_node = nodes.ref("error")
    ref_node = nodes.ref("error")
    body = [nodes.ret(ref_node)]
    func_node = nodes.func("f", nodes.arguments([]), body)
    try_node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), target_node, [func_node])
        ],
    )
    
    declaration = name_declaration.ExceptionHandlerTargetNode("error")
    references = References([
        (target_node, declaration),
        (ref_node, declaration),
        (func_node, name_declaration.VariableDeclarationNode("f")),
    ])
    
    try:
        _updated_bindings(try_node, references)
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(ref_node, error.node)
        assert_is("error", error.name)


@istest
def class_name_is_definitely_bound_after_class_definition():
    node = nodes.class_def("User", [])
    declaration = name_declaration.VariableDeclarationNode("User")
    
    references = References([(node, declaration)])
    
    bindings = _updated_bindings(node, references)
    assert_equal(True, bindings.is_definitely_bound(node))


@istest
def body_of_class_is_checked():
    _assert_child_statement_is_checked(lambda generate:
        generate.class_def("User", [generate.unbound_ref_statement()])
    )


@istest
def type_name_is_definitely_bound_after_type_definition():
    int_ref = nodes.ref("int")
    str_ref = nodes.ref("str")
    
    int_declaration = name_declaration.VariableDeclarationNode("int")
    str_declaration = name_declaration.VariableDeclarationNode("str")
    
    node = nodes.type_definition("Identifier", nodes.type_union([int_ref, str_ref]))
    declaration = name_declaration.TypeDeclarationNode("Identifier")
    
    references = References([
        (node, declaration),
        (int_ref, int_declaration),
        (str_ref, str_declaration),
    ])
    
    bindings = _updated_bindings(node, references, is_definitely_bound={
        int_declaration: True,
        str_declaration: True,
    })
    assert_equal(True, bindings.is_definitely_bound(node))


@istest
def import_name_is_definitely_bound_after_import_statement():
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.Import([alias_node])
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([(alias_node, declaration)])
    
    bindings = _updated_bindings(node, references)
    assert_equal(True, bindings.is_definitely_bound(alias_node))


@istest
def import_name_is_definitely_bound_after_import_from_statement():
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.import_from(["."], [alias_node])
    
    declaration = name_declaration.VariableDeclarationNode("x")
    references = References([(alias_node, declaration)])
    
    bindings = _updated_bindings(node, references)
    assert_equal(True, bindings.is_definitely_bound(alias_node))


_standard_target_node = nodes.ref("x")
_standard_unbound_ref = nodes.ref("unbound_ref")

def _test_context(create_node):
    declaration = name_declaration.VariableDeclarationNode("x")
    
    references = IdentityDict([
        (_standard_target_node, declaration),
        (_standard_unbound_ref, name_declaration.VariableDeclarationNode("unbound_ref")),
    ])
    
    is_definitely_bound = {}
    type_lookup = IdentityDict()
    
    class NodeGenerator(object):
        def target(self):
            target_node = nodes.ref("x")
            references[target_node] = declaration
            return target_node
        
        def assignment(self):
            return nodes.assign([self.target()], nodes.none())
        
        def unbound_ref(self):
            return _standard_unbound_ref
        
        def unbound_ref_statement(self):
            return nodes.expression_statement(self.unbound_ref())
        
        def bound_ref(self, name, type_):
            bound_node = nodes.ref(name)
            bound_declaration = name_declaration.VariableDeclarationNode(name)
            references[bound_node] = bound_declaration
            is_definitely_bound[bound_declaration] = True
            type_lookup[bound_node] = type_
            return bound_node
        
        def func(self, *args, **kwargs):
            node = nodes.func(*args, **kwargs)
            declaration = name_declaration.FunctionDeclarationNode(node.name)
            references[node] = declaration
            return node
        
        def class_def(self, *args, **kwargs):
            node = nodes.class_def(*args, **kwargs)
            declaration = name_declaration.ClassDeclarationNode(node.name)
            references[node] = declaration
            return node
            
            
        
    node = create_node(NodeGenerator())
    
    return node, References(references), is_definitely_bound, TypeLookup(type_lookup)


def _assert_name_is_not_definitely_bound(create_node):
    args = _test_context(create_node)
    bindings = _updated_bindings(*args)
    assert not bindings.is_definitely_bound(_standard_target_node)
    

def _assert_name_is_definitely_bound(create_node):
    args = _test_context(create_node)
    bindings = _updated_bindings(*args)
    assert bindings.is_definitely_bound(_standard_target_node)


def _assert_child_statement_is_checked(create_node):
    _assert_child_expression_is_checked(create_node)


def _assert_child_expression_is_checked(create_node):
    args = _test_context(create_node)
    _assert_is_unbound_error(_standard_unbound_ref, lambda: _updated_bindings(*args))
    

def _updated_bindings(node, references, is_definitely_bound=None, type_lookup=None):
    if is_definitely_bound is None:
        is_definitely_bound = {}
    return check_bindings(
        node,
        references,
        type_lookup=type_lookup,
        is_definitely_bound=is_definitely_bound
    )


def _assert_is_unbound_error(node, func):
    try:
        func()
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(node, error.node)
