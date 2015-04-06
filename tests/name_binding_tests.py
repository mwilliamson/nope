from nose.tools import istest, assert_equal, assert_is

from nope import nodes, errors, name_declaration, types
from nope.name_binding import check_bindings
from nope.identity_dict import NodeDict
from nope.types import TypeLookup
from .inference.util import context_manager_class, SingleScopeReferences
from nope.name_resolution import References


@istest
def children_of_list_comprehension_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.list_comprehension(
            generate.unbound_ref(),
            nodes.comprehension_for(
                generate.bound_ref("x", types.int_type),
                nodes.list_literal([]),
            ),
        )
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.list_comprehension(
            nodes.none(),
            nodes.comprehension_for(
                nodes.attr(generate.unbound_ref(), "x"),
                nodes.list_literal([]),
            ),
        )
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.list_comprehension(
            nodes.none(),
            nodes.comprehension_for(
                generate.bound_ref("x", types.int_type),
                generate.unbound_ref(),
            ),
        )
    )


@istest
def list_comprehension_target_is_definitely_bound():
    node = nodes.list_comprehension(
        nodes.ref("x"),
        nodes.comprehension_for(
            nodes.ref("x"),
            nodes.list_literal([]),
        ),
    )
    
    _updated_bindings(node)


@istest
def variable_is_definitely_bound_after_assignment():
    target_node = nodes.ref("x")
    node = nodes.assign([target_node], nodes.none())
    
    bindings = _updated_bindings(node)
    assert_equal(True, bindings.is_definitely_bound(target_node))


@istest
def value_is_evaluated_before_target_is_bound():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    node = nodes.assign([target_node], ref_node)
    
    _assert_is_unbound_error(ref_node, lambda: _updated_bindings(node))


@istest
def targets_are_evaluated_left_to_right():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    node = nodes.assign([nodes.attr(ref_node, "blah"), target_node], nodes.none())
    
    _assert_is_unbound_error(ref_node, lambda: _updated_bindings(node))


@istest
def variable_in_tuple_is_definitely_bound_after_assignment():
    target_node = nodes.ref("x")
    node = nodes.assign([nodes.tuple_literal([target_node])], nodes.tuple_literal([nodes.none()]))
    
    bindings = _updated_bindings(node)
    assert_equal(True, bindings.is_definitely_bound(target_node))


@istest
def error_if_name_is_unbound():
    ref = nodes.ref("x")
    _assert_is_unbound_error(ref, lambda: _updated_bindings(ref))


@istest
def no_error_if_name_is_definitely_bound():
    ref = nodes.ref("x")
    _updated_bindings(ref, is_definitely_bound={"x": True})


@istest
def declarations_in_exactly_one_if_else_branch_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.if_(nodes.bool_literal(True), [generate.assignment()], [])
    )
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.if_(nodes.bool_literal(True), [], [generate.assignment()])
    )


@istest
def variable_remains_definitely_bound_after_being_reassigned_in_one_branch_of_if_else():
    target_node = nodes.ref("x")
    node = nodes.if_(
        nodes.bool_literal(True),
        [nodes.assign([target_node], nodes.none())],
        []
    )
    
    bindings = _updated_bindings(node, is_definitely_bound={"x": True})
    assert bindings.is_definitely_bound(target_node)


@istest
def declarations_in_both_if_else_branches_are_definitely_bound():
    _assert_name_is_definitely_bound(lambda generate:
        nodes.if_(nodes.bool_literal(True), [generate.assignment()], [generate.assignment()])
    )


@istest
def potentially_bound_variable_becomes_definitely_bound_after_being_assigned_in_both_branches_of_if_else():
    target_node = nodes.ref("x")
    node = nodes.if_(
        nodes.bool_literal(True),
        [nodes.assign([target_node], nodes.none())],
        []
    )
    
    bindings = _updated_bindings(node)
    assert not bindings.is_definitely_bound(target_node)
    
    node = nodes.if_(
        nodes.bool_literal(True),
        [nodes.assign([target_node], nodes.none())],
        [nodes.assign([target_node], nodes.none())]
    )
    bindings = _updated_bindings(node)
    assert bindings.is_definitely_bound(target_node)


@istest
def children_of_if_else_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.if_(
            generate.unbound_ref(),
            [],
            []
        )
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.if_(
            nodes.bool_literal(True),
            [generate.unbound_ref_statement()],
            []
        )
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.if_(
            nodes.bool_literal(True),
            [],
            [generate.unbound_ref_statement()]
        )
    )


@istest
def children_of_while_loop_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.while_(generate.unbound_ref(), [], [])
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.while_(
            nodes.bool_literal(True),
            [generate.unbound_ref_statement()],
            []
        )
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.while_(
            nodes.bool_literal(True),
            [],
            [generate.unbound_ref_statement()]
        )
    )

@istest
def declarations_in_both_body_and_else_body_of_while_loop_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.while_(nodes.bool_literal(True), [generate.assignment()], [generate.assignment()])
    )


@istest
def children_of_for_loop_are_checked():
    _assert_child_expression_is_checked(lambda generate:
        nodes.for_(
            nodes.attr(generate.unbound_ref(), "blah"),
            nodes.list_literal([]),
            [],
            []
        )
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.for_(
            generate.target(),
            generate.unbound_ref(),
            [],
            []
        ),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.for_(
            generate.target(),
            nodes.list_literal([]),
            [generate.unbound_ref_statement()],
            []
        ),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.for_(
            generate.target(),
            nodes.list_literal([]),
            [],
            [generate.unbound_ref_statement()],
        ),
    )

@istest
def for_loop_target_is_defined_but_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.for_(generate.target(), nodes.list_literal([]), [], [])
    )


@istest
def declarations_in_both_body_and_else_body_of_for_loop_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.for_(
            generate.target(),
            nodes.list_literal([]),
            [generate.assignment()],
            [generate.assignment()]
        ),
    )


@istest
def children_of_try_statement_are_checked():
    _assert_child_statement_is_checked(lambda generate:
        nodes.try_([generate.unbound_ref_statement()]),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.try_([], handlers=[
            nodes.except_(None, None, [generate.unbound_ref_statement()])
        ]),
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.try_([], handlers=[
            nodes.except_(generate.unbound_ref(), None, [])
        ]),
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.try_([], handlers=[
            nodes.except_(nodes.none(), nodes.attr(generate.unbound_ref(), "blah"), [])
        ]),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.try_([], finally_body=[
            generate.unbound_ref_statement()
        ]),
    )


@istest
def declarations_in_body_and_handler_body_and_finally_body_of_try_statement_are_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.try_(
            [generate.assignment()],
            handlers=[
                nodes.except_(None, None, [generate.assignment()])
            ],
            finally_body=[generate.assignment()],
        )
    )


@istest
def except_handler_target_is_defined_but_not_definitely_bound():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.try_(
            [],
            handlers=[
                nodes.except_(nodes.none(), generate.target(), [])
            ],
        )
    )


@istest
def except_handler_targets_in_same_try_statement_can_share_their_name():
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.try_(
            [],
            handlers=[
                nodes.except_(nodes.none(), generate.target(), []),
                nodes.except_(nodes.none(), generate.target(), []),
            ],
        )
    )


@istest
def except_handler_targets_cannot_share_their_name_when_nested():
    first_target_node = nodes.ref("error")
    second_target_node = nodes.ref("error")
    node = nodes.try_(
        [],
        handlers=[
            nodes.except_(nodes.none(), first_target_node, [
                nodes.try_(
                    [],
                    handlers=[
                        nodes.except_(nodes.none(), second_target_node, [])
                    ],
                )
            ])
        ],
    )
    
    try:
        _updated_bindings(node)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal(second_target_node, error.node)
        assert_equal("cannot reuse the same name for nested exception handler targets", str(error))


@istest
def children_of_with_statement_are_checked():
    context_manager_type = context_manager_class(exit_type=types.none_type)
    
    _assert_child_expression_is_checked(lambda generate:
        nodes.with_(
            generate.unbound_ref(),
            None,
            []
        ),
    )
    _assert_child_expression_is_checked(lambda generate:
        nodes.with_(
            generate.bound_ref("manager", context_manager_type),
            nodes.attr(generate.unbound_ref(), "blah"),
            []
        ),
    )
    _assert_child_statement_is_checked(lambda generate:
        nodes.with_(
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
    statement = nodes.with_(manager_ref, target_ref, [nodes.expression_statement(var_ref)])
    
    _updated_bindings(
        statement,
        is_definitely_bound={"manager": True},
        type_lookup=TypeLookup(NodeDict([(manager_ref, context_manager_class(exit_type=types.none_type))]))
    )


@istest
def assigned_variables_in_with_statement_body_are_still_bound_after_exit_if_exit_method_always_returns_none():
    context_manager_type = context_manager_class(exit_type=types.none_type)
    _assert_name_is_definitely_bound(lambda generate:
        nodes.with_(
            generate.bound_ref("manager", context_manager_type),
            None,
            [generate.assignment()]
        ),
    )


@istest
def assigned_variables_in_with_statement_body_are_unbound_after_exit_if_exit_method_does_not_return_none():
    context_manager_type = context_manager_class(exit_type=types.bool_type)
    _assert_name_is_not_definitely_bound(lambda generate:
        nodes.with_(
            generate.bound_ref("manager", context_manager_type),
            None,
            [generate.assignment()]
        ),
    )


@istest
def function_name_is_definitely_bound_after_function_definition():
    node = nodes.func("f", nodes.arguments([]), [], type=None)
    
    bindings = _updated_bindings(node)
    assert_equal(True, bindings.is_definitely_bound(node))


@istest
def function_can_be_referenced_immediately_after_definition():
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[])
    _updated_bindings(nodes.module([f, nodes.expression_statement(nodes.ref("f"))]))


@istest
def function_cannot_be_referenced_before_definition():
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[])
    ref_node = nodes.ref("f")
    
    try:
        _updated_bindings(nodes.module([
            nodes.expression_statement(ref_node),
            f,
        ]))
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(ref_node, error.node)


@istest
def function_cannot_be_referenced_before_definition_of_dependencies():
    g_ref = nodes.ref("g")
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(g_ref, []))
    ])
    g = nodes.func("g", type=None, args=nodes.Arguments([]), body=[])
    
    try:
        _updated_bindings(nodes.module([
            f,
            nodes.expression_statement(nodes.ref("f")),
            g,
        ]))
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(g_ref, error.node)


@istest
def function_definitions_in_statement_lists_can_be_defined_out_of_order():
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(nodes.ref("g"), []))
    ])
    g = nodes.func("g", type=None, args=nodes.Arguments([]), body=[])
    
    _updated_bindings(nodes.module([f, g]))


@istest
def function_definitions_can_be_mutually_recursive():
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(nodes.ref("g"), []))
    ])
    g = nodes.func("g", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(nodes.ref("f"), []))
    ])
    
    _updated_bindings(nodes.module([f, g]))


@istest
def body_of_function_is_checked():
    _assert_child_statement_is_checked(lambda generate:
        generate.func("f", nodes.arguments([]), [generate.unbound_ref_statement()], type=None)
    )


@istest
def variables_from_outer_scope_remain_bound():
    ref = nodes.ref("x")
    func_node = nodes.func("f", nodes.arguments([]), [nodes.expression_statement(ref)], type=None)
    
    _updated_bindings(func_node, is_definitely_bound={"x": True})


@istest
def arguments_of_function_are_definitely_bound():
    arg = nodes.arg("x")
    arg_ref = nodes.ref("x")
    func_node = nodes.func("f", nodes.arguments([arg]), [nodes.expression_statement(arg_ref)], type=None)
    
    _updated_bindings(func_node)


@istest
def type_parameters_of_function_are_definitely_bound():
    param = nodes.formal_type_parameter("T")
    arg_ref = nodes.ref("T")
    returns_ref = nodes.ref("T")
    explicit_type = nodes.signature(type_params=[param], args=[nodes.signature_arg(arg_ref)], returns=returns_ref)
    func_node = nodes.func("f", nodes.arguments([]), [], type=explicit_type)
    
    _updated_bindings(func_node)


@istest
def exception_handler_targets_cannot_be_accessed_from_nested_function():
    target_node = nodes.ref("error")
    ref_node = nodes.ref("error")
    body = [nodes.ret(ref_node)]
    func_node = nodes.func("f", nodes.arguments([]), body, type=None)
    try_node = nodes.try_(
        [],
        handlers=[
            nodes.except_(nodes.none(), target_node, [func_node])
        ],
    )
    
    declaration = name_declaration.ExceptionHandlerTargetNode("error")
    references = References([
        (target_node, declaration),
        (ref_node, declaration),
        (func_node, name_declaration.VariableDeclarationNode("f")),
    ])
    
    try:
        _updated_bindings(try_node, references=references)
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(ref_node, error.node)
        assert_is("error", error.name)


@istest
def class_name_is_definitely_bound_after_class_definition():
    node = nodes.class_("User", [])
    bindings = _updated_bindings(node)
    assert_equal(True, bindings.is_definitely_bound(node))


@istest
def method_can_reference_later_function_if_class_is_not_used_in_the_interim():
    g_ref = nodes.ref("g")
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(g_ref, []))
    ])
    g = nodes.func("g", type=None, args=nodes.Arguments([]), body=[])
    
    _updated_bindings(nodes.module([
        nodes.class_("a", [f]),
        g,
    ]))


@istest
def class_cannot_be_referenced_if_method_dependencies_are_not_bound():
    g_ref = nodes.ref("g")
    f = nodes.func("f", type=None, args=nodes.Arguments([]), body=[
        nodes.ret(nodes.call(g_ref, []))
    ])
    g = nodes.func("g", type=None, args=nodes.Arguments([]), body=[])
    
    try:
        _updated_bindings(nodes.module([
            nodes.class_("a", [f]),
            nodes.expression_statement(nodes.ref("a")),
            g,
        ]))
        assert False, "Expected error"
    except errors.UnboundLocalError as error:
        assert_equal(g_ref, error.node)


@istest
def body_of_class_is_checked():
    _assert_child_statement_is_checked(lambda generate:
        generate.class_def("User", [generate.unbound_ref_statement()])
    )


@istest
def type_name_is_definitely_bound_after_type_definition():
    int_ref = nodes.ref("int")
    str_ref = nodes.ref("str")
    
    node = nodes.type_definition("Identifier", nodes.type_union([int_ref, str_ref]))
    
    bindings = _updated_bindings(node, is_definitely_bound=["int", "str"])
    assert_equal(True, bindings.is_definitely_bound(node))


@istest
def import_name_is_definitely_bound_after_import_statement():
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.Import([alias_node])
    
    bindings = _updated_bindings(node)
    assert_equal(True, bindings.is_definitely_bound(alias_node))


@istest
def import_name_is_definitely_bound_after_import_from_statement():
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.import_from(["."], [alias_node])
    
    bindings = _updated_bindings(node)
    assert_equal(True, bindings.is_definitely_bound(alias_node))


_standard_target_node = nodes.ref("x")
_standard_unbound_ref = nodes.ref("unbound_ref")

def _test_context(create_node):
    is_definitely_bound = {}
    type_lookup = NodeDict()
    
    class NodeGenerator(object):
        def target(self):
            return nodes.ref("x")
        
        def assignment(self):
            return nodes.assign([self.target()], nodes.none())
        
        def unbound_ref(self):
            return _standard_unbound_ref
        
        def unbound_ref_statement(self):
            return nodes.expression_statement(self.unbound_ref())
        
        def bound_ref(self, name, type_):
            bound_node = nodes.ref(name)
            is_definitely_bound[name] = True
            type_lookup[bound_node] = type_
            return bound_node
        
        def func(self, *args, **kwargs):
            return nodes.func(*args, **kwargs)
        
        def class_def(self, *args, **kwargs):
            return nodes.class_(*args, **kwargs)
            
        
    node = create_node(NodeGenerator())
    
    return {
        "node": node,
        "is_definitely_bound": is_definitely_bound,
        "type_lookup": TypeLookup(type_lookup),
    }


def _assert_name_is_not_definitely_bound(create_node):
    args = _test_context(create_node)
    bindings = _updated_bindings(**args)
    assert not bindings.is_definitely_bound(_standard_target_node)
    

def _assert_name_is_definitely_bound(create_node):
    args = _test_context(create_node)
    bindings = _updated_bindings(**args)
    assert bindings.is_definitely_bound(_standard_target_node)


def _assert_child_statement_is_checked(create_node):
    _assert_child_expression_is_checked(create_node)


def _assert_child_expression_is_checked(create_node):
    args = _test_context(create_node)
    _assert_is_unbound_error(_standard_unbound_ref, lambda: _updated_bindings(**args))
    

def _updated_bindings(node, *, references=None, is_definitely_bound=None, type_lookup=None):
    if is_definitely_bound is None:
        is_definitely_bound = {}
    
    if references is None:
        references = SingleScopeReferences()
    
    is_definitely_bound = dict(
        (references.declaration(name), True)
        for name in is_definitely_bound
    )
    
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
