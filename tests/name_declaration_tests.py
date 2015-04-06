from nose.tools import istest, assert_equal

from nope import nodes, errors, name_declaration
from nope.name_declaration import Declarations, DeclarationFinder, _declare as declare


@istest
def assignment_adds_declaration_to_declarations():
    declarations = _new_declarations()
    definition_node = nodes.ref("x")
    node = nodes.assign([definition_node], nodes.none())
    declare(node, declarations)
    assert_equal("x", declarations.declaration("x").name)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)


@istest
def assignment_to_tuple_declares_variables_in_tuple():
    declarations = _new_declarations()
    first_definition_node = nodes.ref("x")
    second_definition_node = nodes.ref("y")
    node = nodes.assign([nodes.tuple_literal([first_definition_node, second_definition_node])], nodes.none())
    declare(node, declarations)
    assert_equal("x", declarations.declaration("x").name)
    assert_equal("y", declarations.declaration("y").name)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)
    assert isinstance(declarations.declaration("y"), name_declaration.VariableDeclarationNode)


@istest
def for_loop_target_is_declared():
    declarations = _new_declarations()
    node = nodes.for_(nodes.ref("target"), nodes.list_literal([]), [], [])
    declare(node, declarations)
    assert_equal("target", declarations.declaration("target").name)
    assert isinstance(declarations.declaration("target"), name_declaration.VariableDeclarationNode)


@istest
def except_handler_target_is_declared():
    declarations = _new_declarations()
    node = nodes.try_(
        [],
        handlers=[
            nodes.except_(nodes.none(), nodes.ref("error"), [])
        ],
    )
    declare(node, declarations)
    assert_equal("error", declarations.declaration("error").name)
    assert isinstance(declarations.declaration("error"), name_declaration.ExceptionHandlerTargetNode)


@istest
def with_statement_target_is_declared():
    declarations = _new_declarations()
    node = nodes.with_(nodes.ref("manager"), nodes.ref("target"), [])
    declare(node, declarations)
    assert_equal("target", declarations.declaration("target").name)
    assert isinstance(declarations.declaration("target"), name_declaration.VariableDeclarationNode)


@istest
def with_statement_target_can_be_none():
    declarations = _new_declarations()
    node = nodes.with_(nodes.ref("manager"), None, [])
    declare(node, declarations)


@istest
def function_definition_is_declared():
    node = nodes.func("f", nodes.arguments([]), [], type=None)
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert_equal("f", declarations.declaration("f").name)
    assert isinstance(declarations.declaration("f"), name_declaration.FunctionDeclarationNode)


@istest
def names_in_function_are_not_declared():
    node = nodes.func("f", nodes.arguments([]), [
        nodes.assign([nodes.ref("x")], nodes.none())
    ], type=None)
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert not declarations.is_declared("x")


@istest
def names_in_function_signature_are_not_declared():
    explicit_type = nodes.signature(
        type_params=[nodes.formal_type_parameter("T")],
        args=[],
        returns=nodes.ref("T"),
    )
    node = nodes.func("f", nodes.arguments([]), [], type=explicit_type)
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert not declarations.is_declared("T")


@istest
def class_definition_is_declared():
    node = nodes.class_("User", [])
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert_equal("User", declarations.declaration("User").name)
    assert isinstance(declarations.declaration("User"), name_declaration.ClassDeclarationNode)


@istest
def names_in_class_are_not_declared():
    node = nodes.class_("User", [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert not declarations.is_declared("x")


@istest
def type_definition_is_declared():
    node = nodes.type_definition("Identifier", nodes.type_union([nodes.ref("int"), nodes.ref("str")]))
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert_equal("Identifier", declarations.declaration("Identifier").name)
    assert isinstance(declarations.declaration("Identifier"), name_declaration.TypeDeclarationNode)


@istest
def formal_type_parameter_is_declared():
    node = nodes.formal_type_parameter("T")
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert_equal("T", declarations.declaration("T").name)
    assert isinstance(declarations.declaration("T"), name_declaration.TypeDeclarationNode)


@istest
def argument_adds_declaration_to_declarations():
    declarations = _new_declarations()
    node = nodes.arg("x")
    declare(node, declarations)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)


@istest
def import_name_is_declared():
    declarations = _new_declarations()
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.Import([alias_node])
    declare(node, declarations)
    assert_equal("x", declarations.declaration("x").name)
    assert isinstance(declarations.declaration("x"), name_declaration.ImportDeclarationNode)


@istest
def import_from_name_is_declared():
    declarations = _new_declarations()
    alias_node = nodes.import_alias("x", None)
    node = nodes.import_from(["."], [alias_node])
    declare(node, declarations)
    assert_equal("x", declarations.declaration("x").name)
    assert isinstance(declarations.declaration("x"), name_declaration.ImportDeclarationNode)


@istest
def import_from_alias_name_is_declared():
    declarations = _new_declarations()
    alias_node = nodes.import_alias("x", "y")
    node = nodes.import_from(["."], [alias_node])
    declare(node, declarations)
    assert_equal("y", declarations.declaration("y").name)
    assert isinstance(declarations.declaration("y"), name_declaration.ImportDeclarationNode)
    assert not declarations.is_declared("x")


@istest
def cannot_declare_name_with_two_different_declaration_types():
    declarations = _new_declarations()
    node = nodes.assign([nodes.ref("f")], nodes.none())
    declare(node, declarations)
    node = nodes.func("f", nodes.arguments([]), [], type=None)
    try:
        declare(node, declarations)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal("function declaration and variable assignment cannot share the same name", str(error))


@istest
def _declarations_in_include_declarations_in_body():
    node = nodes.func("f", nodes.arguments([]), [
        nodes.assign([nodes.ref("x")], nodes.none())
    ], type=None)
    
    declarations = _declarations_in(node)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)
    assert not declarations.is_declared("f")


@istest
def _declarations_in_include_type_parameter_declarations():
    explicit_type = nodes.signature(type_params=[nodes.formal_type_parameter("T")], args=[], returns=nodes.ref("none"))
    node = nodes.func("f", nodes.arguments([]), [], type=explicit_type)
    
    declarations = _declarations_in(node)
    assert isinstance(declarations.declaration("T"), name_declaration.TypeDeclarationNode)


@istest
def no_error_if_explicit_type_for_function_is_not_signature():
    node = nodes.func("f", nodes.arguments([]), [], type=nodes.ref("T"))
    _declarations_in(node)


@istest
def _declarations_in_include_argument_declarations():
    node = nodes.func("f", nodes.arguments([nodes.arg("x")]), [], type=None)
    
    declarations = _declarations_in(node)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)
    assert not declarations.is_declared("f")


@istest
def _declarations_in_include_declarations_in_body():
    node = nodes.class_("User", [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    declarations = _declarations_in(node)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)
    assert not declarations.is_declared("User")


@istest
def _declarations_in_include_self_class():
    node = nodes.class_("User", [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    declarations = _declarations_in(node)
    assert isinstance(declarations.declaration("Self"), name_declaration.SelfTypeDeclarationNode)


@istest
def _declarations_in_include_formal_type_parameters():
    node = nodes.class_("Option", [], type_params=[nodes.formal_type_parameter("T")])
    
    declarations = _declarations_in(node)
    assert isinstance(declarations.declaration("T"), name_declaration.TypeDeclarationNode)


@istest
def declarations_in_list_comprehension_are_variable_reference_targets():
    node = nodes.list_comprehension(
        nodes.none(),
        nodes.tuple_literal([nodes.ref("target"), nodes.attr(nodes.ref("other"), "name")]),
        nodes.ref("iterable")
    )
    
    declarations = _declarations_in(node)
    assert isinstance(declarations.declaration("target"), name_declaration.VariableDeclarationNode)
    assert not declarations.is_declared("other")
    assert not declarations.is_declared("iterable")
    
    

def _new_declarations():
    return Declarations({})


def _declarations_in(*args, **kwargs):
    finder = DeclarationFinder()
    return finder.declarations_in(*args, **kwargs)
