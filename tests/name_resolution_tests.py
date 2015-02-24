from nose.tools import istest, assert_is, assert_is_not, assert_equal

from nope import nodes, errors
from nope.name_declaration import VariableDeclarationNode, DeclarationFinder, Declarations
from nope.name_resolution import NameResolver


@istest
def none_has_no_references():
    _assert_no_references(nodes.none())


@istest
def bool_has_no_references():
    _assert_no_references(nodes.bool_literal(True))


@istest
def int_has_no_references():
    _assert_no_references(nodes.int_literal(4))


@istest
def str_has_no_references():
    _assert_no_references(nodes.str_literal(""))


@istest
def variable_reference_has_name_resolved():
    ref = nodes.ref("x")
    declarations = _create_declarations(["x"])
    references = resolve(ref, declarations)
    
    assert_is(declarations.declaration("x"), references.referenced_declaration(ref))


@istest
def error_if_name_is_undefined():
    ref = nodes.ref("x")
    declarations = _create_declarations([])
    try:
        resolve(ref, declarations)
        assert False, "Expected error"
    except errors.UndefinedNameError as error:
        assert_is(ref, error.node)
        assert_is("x", error.name)


@istest
def list_expression_has_names_in_elements_resolved():
    _assert_children_resolved(
        lambda ref: nodes.list_literal([ref]),
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
        lambda ref: nodes.if_(ref, [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.if_(nodes.bool_literal(True), [nodes.expression_statement(ref)], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.if_(nodes.bool_literal(True), [], [nodes.expression_statement(ref)]),
    )


@istest
def while_loop_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.while_(ref, [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.while_(nodes.bool_literal(True), [nodes.expression_statement(ref)], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.while_(nodes.bool_literal(True), [], [nodes.expression_statement(ref)]),
    )


@istest
def for_loop_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.for_loop(ref, nodes.list_literal([]), [], []),
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), ref, [], []),
        other_names=["target"]
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), nodes.list_literal([]), [nodes.expression_statement(ref)], []),
        other_names=["target"]
    )
    _assert_children_resolved(
        lambda ref: nodes.for_loop(nodes.ref("target"), nodes.list_literal([]), [], [nodes.expression_statement(ref)]),
        other_names=["target"]
    )


@istest
def break_has_no_references():
    _assert_no_references(nodes.break_())


@istest
def continue_has_no_references():
    _assert_no_references(nodes.continue_())


@istest
def try_statement_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.try_([nodes.expression_statement(ref)]),
    )
    _assert_children_resolved(
        lambda ref: nodes.try_([], handlers=[
            nodes.except_(None, None, [nodes.expression_statement(ref)])
        ]),
    )
    _assert_children_resolved(
        lambda ref: nodes.try_([], handlers=[
            nodes.except_(ref, None, [])
        ]),
    )
    _assert_children_resolved(
        lambda ref: nodes.try_([], handlers=[
            nodes.except_(nodes.ref("Exception"), ref, [])
        ]),
        other_names=["Exception"],
    )
    _assert_children_resolved(
        lambda ref: nodes.try_([], finally_body=[
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
        lambda ref: nodes.assert_statement(nodes.bool_literal(False), ref),
    )
    
    
@istest
def list_comprehension_has_child_names_resolved():
    _assert_children_resolved(
        lambda ref: nodes.list_comprehension(ref, nodes.comprehension(nodes.none(), nodes.none())),
    )
    _assert_children_resolved(
        lambda ref: nodes.list_comprehension(nodes.none(), nodes.comprehension(nodes.attr(ref, "name"), nodes.none())),
    )
    _assert_children_resolved(
        lambda ref: nodes.list_comprehension(nodes.none(), nodes.comprehension(nodes.none(), ref)),
    )
    

@istest
def list_comprehension_adds_target_names_to_body_context():
    target = nodes.ref("target")
    ref = nodes.ref("target")
    node = nodes.list_comprehension(
        target,
        nodes.comprehension(ref, nodes.none())
    )
    
    declarations = _create_declarations([])
    references = resolve(node, declarations)
    assert not declarations.is_declared("target")
    assert_is(references.referenced_declaration(target), references.referenced_declaration(ref))
    

@istest
def list_comprehension_generator_is_not_in_same_scope_as_element():
    target = nodes.ref("target")
    ref = nodes.ref("target")
    iterable = nodes.ref("target")
    node = nodes.list_comprehension(
        target,
        nodes.comprehension(ref, iterable)
    )
    
    declarations = _create_declarations(["target"])
    references = resolve(node, declarations)
    assert_is_not(references.referenced_declaration(target), references.referenced_declaration(iterable))


@istest
def function_definition_signature_has_names_resolved():
    int_ref = nodes.ref("int")
    str_ref = nodes.ref("str")
    
    signature = nodes.signature(
        args=[nodes.signature_arg(int_ref)],
        returns=str_ref,
    )
    node = nodes.typed(signature, nodes.func("f", nodes.arguments([]), []))
    
    declarations = _create_declarations(["f", "int", "str"])
    references = resolve(node, declarations)
    assert_is(declarations.declaration("int"), references.referenced_declaration(int_ref))
    assert_is(declarations.declaration("str"), references.referenced_declaration(str_ref))


@istest
def generic_function_definition_signature_has_names_resolved():
    param = nodes.formal_type_parameter("T")
    arg_ref = nodes.ref("T")
    return_ref = nodes.ref("T")
    
    signature = nodes.signature(
        type_params=[param],
        args=[nodes.signature_arg(arg_ref)],
        returns=return_ref,
    )
    node = nodes.typed(signature, nodes.func("f", nodes.arguments([]), []))
    
    declarations = _create_declarations(["f"])
    references = resolve(node, declarations)
    assert not declarations.is_declared("T")
    assert_is(references.referenced_declaration(param), references.referenced_declaration(arg_ref))
    assert_is(references.referenced_declaration(param), references.referenced_declaration(return_ref))
    

@istest
def function_definitions_adds_function_name_to_context():
    node = nodes.func("f", nodes.arguments([]), [])
    
    declarations = _create_declarations(["f"])
    references = resolve(node, declarations)
    assert_is(declarations.declaration("f"), references.referenced_declaration(node))


@istest
def function_definitions_adds_argument_names_to_body_context():
    arg = nodes.argument("x")
    args = nodes.arguments([arg])
    ref = nodes.ref("x")
    body = [nodes.ret(ref)]
    node = nodes.func("f", args, body)
    
    declarations = _create_declarations(["f"])
    references = resolve(node, declarations)
    assert not declarations.is_declared("x")
    assert_is(references.referenced_declaration(arg), references.referenced_declaration(ref))


@istest
def function_definitions_bodies_can_access_variables_from_outer_scope():
    args = nodes.arguments([])
    ref = nodes.ref("x")
    body = [nodes.ret(ref)]
    node = nodes.func("f", args, body)
    
    declarations = _create_declarations(["x", "f"])
    
    references = resolve(node, declarations)
    assert_is(declarations.declaration("x"), references.referenced_declaration(ref))


@istest
def function_definitions_arguments_shadow_variables_of_same_name_in_outer_scope():
    arg = nodes.argument("x")
    args = nodes.arguments([arg])
    ref = nodes.ref("x")
    body = [nodes.ret(ref)]
    node = nodes.func("f", args, body)
    
    declarations = _create_declarations(["x", "f"])
    
    references = resolve(node, declarations)
    assert_is(references.referenced_declaration(arg), references.referenced_declaration(ref))
    assert_is_not(declarations.declaration("x"), references.referenced_declaration(ref))


@istest
def function_definitions_assignments_shadow_variables_of_same_name_in_outer_scope():
    args = nodes.arguments([])
    ref = nodes.ref("x")
    body = [nodes.assign([ref], nodes.none())]
    node = nodes.func("f", args, body)
    
    declarations = _create_declarations(["x", "f"])
    
    references = resolve(node, declarations)
    assert_is_not(declarations.declaration("x"), references.referenced_declaration(ref))


@istest
def class_definition_is_resolved_to_class_declaration():
    node = nodes.class_("User", [])
    
    declarations = _create_declarations(["User"])
    references = resolve(node, declarations)
    assert_is(declarations.declaration("User"), references.referenced_declaration(node))
    

@istest
def class_definition_base_classes_are_resolved():
    ref = nodes.ref("object")
    node = nodes.class_("User", [], base_classes=[ref])
    
    declarations = _create_declarations(["User", "object"])
    references = resolve(node, declarations)
    assert_is(declarations.declaration("object"), references.referenced_declaration(ref))


@istest
def class_definition_bodies_can_access_variables_from_outer_scope():
    ref = nodes.ref("x")
    node = nodes.class_("User", [nodes.expression_statement(ref)])
    
    declarations = _create_declarations(["x", "User"])
    
    references = resolve(node, declarations)
    assert_is(declarations.declaration("x"), references.referenced_declaration(ref))


@istest
def class_definitions_assignments_shadow_variables_of_same_name_in_outer_scope():
    ref = nodes.ref("x")
    body = [nodes.assign([ref], nodes.none())]
    node = nodes.class_("User", body)
    
    declarations = _create_declarations(["x", "User"])
    
    references = resolve(node, declarations)
    assert_is_not(declarations.declaration("x"), references.referenced_declaration(ref))


@istest
def class_definition_functions_ignore_class_scope_when_resolving_references():
    ref = nodes.ref("x")
    node = nodes.class_("User", [
        nodes.assign([nodes.ref("x")], nodes.none()),
        nodes.func("f", nodes.args([]), [nodes.ret(ref)]),
    ])
    
    declarations = _create_declarations(["x", "User"])
    
    references = resolve(node, declarations)
    assert_is(declarations.declaration("x"), references.referenced_declaration(ref))


@istest
def type_definition_is_resolved_to_type_declaration():
    node = nodes.type_definition("Identifier", nodes.type_union([nodes.ref("int"), nodes.ref("str")]))
    
    declarations = _create_declarations(["Identifier", "int", "str"])
    references = resolve(node, declarations)
    assert_is(declarations.declaration("Identifier"), references.referenced_declaration(node))


@istest
def formal_type_parameter_is_resolved_to_type_declaration():
    node = nodes.formal_type_parameter("T")
    
    declarations = _create_declarations(["T"])
    references = resolve(node, declarations)
    assert_is(declarations.declaration("T"), references.referenced_declaration(node))


@istest
def import_multiple_aliases_using_same_name_resolve_to_same_node():
    declarations = _create_declarations(["x"])
    first_alias_node = nodes.import_alias("x.y", None)
    second_alias_node = nodes.import_alias("x", None)
    node = nodes.Import([first_alias_node, second_alias_node])
    references = resolve(node, declarations)
    assert_is(references.referenced_declaration(first_alias_node), references.referenced_declaration(second_alias_node))


@istest
def import_from_aliases_are_resolved():
    declarations = _create_declarations(["x"])
    alias_node = nodes.import_alias("x", None)
    node = nodes.import_from(["."], [alias_node])
    references = resolve(node, declarations)
    assert_equal(declarations.declaration("x"), references.referenced_declaration(alias_node))


@istest
def names_in_module_are_defined_and_resolved():
    target_node = nodes.ref("x")
    ref_node = nodes.ref("x")
    
    node = nodes.module([
        nodes.assign([target_node], nodes.none()),
        nodes.expression_statement(ref_node),
    ])
    
    declarations = _create_declarations(["x"])
    
    references = resolve(node, declarations)
    assert_is(references.referenced_declaration(ref_node), references.referenced_declaration(target_node))
    


def _create_declarations(names):
    declarations = {}
    for name in names:
        declarations[name] = VariableDeclarationNode(name)
    return Declarations(declarations)


def resolve(node, declarations):
    declaration_finder = DeclarationFinder()
    resolver = NameResolver(declaration_finder, declarations)
    return resolver.resolve(node)


def _assert_no_references(node):
    resolve(node, None)


def _assert_children_resolved(create_node, other_names=None):
    if other_names is None:
        other_names = []
    
    declarations = _create_declarations(["x"] + other_names)
    
    ref = nodes.ref("x")
    references = resolve(create_node(ref), declarations)
    
    assert_is(declarations.declaration("x"), references.referenced_declaration(ref))
