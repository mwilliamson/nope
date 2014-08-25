from nose.tools import istest, assert_is, assert_is_not, assert_equal

from nope import nodes, errors, name_declaration
from nope.name_declaration import declare, declarations_in_function, Context


@istest
def assignment_adds_declaration_to_context():
    context = _new_context()
    definition_node = nodes.ref("x")
    node = nodes.assign([definition_node], nodes.none())
    declare(node, context)
    assert_equal("x", context.declaration("x").name)
    assert isinstance(context.declaration("x"), name_declaration.VariableDeclarationNode)


@istest
def for_loop_target_is_declared():
    context = _new_context()
    node = nodes.for_loop(nodes.ref("target"), nodes.list([]), [], [])
    declare(node, context)
    assert_equal("target", context.declaration("target").name)
    assert isinstance(context.declaration("target"), name_declaration.VariableDeclarationNode)


@istest
def except_handler_target_is_declared():
    context = _new_context()
    node = nodes.try_statement(
        [],
        handlers=[
            nodes.except_handler(nodes.none(), nodes.ref("error"), [])
        ],
    )
    declare(node, context)
    assert_equal("error", context.declaration("error").name)
    assert isinstance(context.declaration("error"), name_declaration.ExceptionHandlerTargetNode)


@istest
def function_definition_is_declared():
    node = nodes.func("f", None, nodes.arguments([]), [])
    
    context = _new_context()
    declare(node, context)
    assert_equal("f", context.declaration("f").name)
    assert isinstance(context.declaration("f"), name_declaration.FunctionDeclarationNode)


@istest
def names_in_function_are_not_declared():
    node = nodes.func("f", None, nodes.arguments([]), [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    context = _new_context()
    declare(node, context)
    assert not context.is_declared("x")


@istest
def names_in_function_are_not_declared():
    node = nodes.func("f", None, nodes.arguments([]), [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    context = _new_context()
    declare(node, context)
    assert not context.is_declared("x")


@istest
def argument_adds_declaration_to_context():
    context = _new_context()
    node = nodes.arg("x")
    declare(node, context)
    assert isinstance(context.declaration("x"), name_declaration.VariableDeclarationNode)


@istest
def import_name_is_declared():
    context = _new_context()
    alias_node = nodes.import_alias("x.y", None)
    node = nodes.Import([alias_node])
    declare(node, context)
    assert_equal("x", context.declaration("x").name)
    assert isinstance(context.declaration("x"), name_declaration.ImportDeclarationNode)


@istest
def import_from_name_is_declared():
    context = _new_context()
    alias_node = nodes.import_alias("x", None)
    node = nodes.import_from(["."], [alias_node])
    declare(node, context)
    assert_equal("x", context.declaration("x").name)
    assert isinstance(context.declaration("x"), name_declaration.ImportDeclarationNode)


@istest
def import_from_alias_name_is_declared():
    context = _new_context()
    alias_node = nodes.import_alias("x", "y")
    node = nodes.import_from(["."], [alias_node])
    declare(node, context)
    assert_equal("y", context.declaration("y").name)
    assert isinstance(context.declaration("y"), name_declaration.ImportDeclarationNode)
    assert not context.is_declared("x")


@istest
def cannot_declare_name_with_two_different_declaration_types():
    context = _new_context()
    node = nodes.assign([nodes.ref("f")], nodes.none())
    declare(node, context)
    node = nodes.func("f", None, nodes.arguments([]), [])
    try:
        declare(node, context)
        assert False, "Expected error"
    except errors.InvalidReassignmentError as error:
        assert_equal("function declaration and variable assignment cannot share the same name", str(error))


@istest
def declarations_in_function_include_declarations_in_body():
    node = nodes.func("f", None, nodes.arguments([]), [
        nodes.assign([nodes.ref("x")], nodes.none())
    ])
    
    context = _new_context()
    declarations = declarations_in_function(node)
    assert isinstance(declarations["x"], name_declaration.VariableDeclarationNode)
    assert "f" not in declarations


@istest
def declarations_in_function_include_argument_declarations():
    node = nodes.func("f", None, nodes.arguments([nodes.arg("x")]), [])
    
    context = _new_context()
    declarations = declarations_in_function(node)
    assert isinstance(declarations["x"], name_declaration.VariableDeclarationNode)
    assert "f" not in declarations
    

def _new_context():
    return Context({})
