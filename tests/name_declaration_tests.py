from nose.tools import istest, assert_is, assert_is_not, assert_equal

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
def for_loop_target_is_declared():
    declarations = _new_declarations()
    node = nodes.for_loop(nodes.ref("target"), nodes.list([]), [], [])
    declare(node, declarations)
    assert_equal("target", declarations.declaration("target").name)
    assert isinstance(declarations.declaration("target"), name_declaration.VariableDeclarationNode)


@istest
def except_handler_target_is_declared():
    declarations = _new_declarations()
    node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), nodes.ref("error"), [])
        ],
    )
    declare(node, declarations)
    assert_equal("error", declarations.declaration("error").name)
    assert isinstance(declarations.declaration("error"), name_declaration.ExceptionHandlerTargetNode)


@istest
def function_definition_is_declared():
    node = nodes.func("f", None, nodes.arguments([]), [])
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert_equal("f", declarations.declaration("f").name)
    assert isinstance(declarations.declaration("f"), name_declaration.FunctionDeclarationNode)


@istest
def names_in_function_are_not_declared():
    node = nodes.func("f", None, nodes.arguments([]), [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    declarations = _new_declarations()
    declare(node, declarations)
    assert not declarations.is_declared("x")


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
    node = nodes.func("f", None, nodes.arguments([]), [])
    try:
        declare(node, declarations)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal("function declaration and variable assignment cannot share the same name", str(error))


@istest
def declarations_in_function_include_declarations_in_body():
    node = nodes.func("f", None, nodes.arguments([]), [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    declarations = declarations_in_function(node)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)
    assert not declarations.is_declared("f")


@istest
def declarations_in_function_include_argument_declarations():
    node = nodes.func("f", None, nodes.arguments([nodes.arg("x")]), [])
    
    declarations = declarations_in_function(node)
    assert isinstance(declarations.declaration("x"), name_declaration.VariableDeclarationNode)
    assert not declarations.is_declared("f")
    

def _new_declarations():
    return Declarations({})

_finder = DeclarationFinder()
declarations_in_function = _finder.declarations_in_function
