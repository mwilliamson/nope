from nose.tools import istest, assert_equal

from nope import parser, nodes

@istest
def module_is_executable_if_it_has_shebang():
    source = """#!/usr/bin/env python
print(1)
"""
    
    module_node = parser.parse(source)
    assert module_node.is_executable


@istest
def module_is_not_executable_if_it_is_missing_shebang():
    source = """print(1)
"""
    
    module_node = parser.parse(source)
    assert not module_node.is_executable


@istest
def can_parse_import_from_in_current_package_and_one_name():
    source = """
from . import message
"""
    
    module_node = parser.parse(source)
    expected_node = nodes.import_from(["."], [nodes.import_alias("message", None)])
    assert_equal(expected_node, module_node.body[0])


@istest
def can_parse_import_alias():
    source = """
from . import message as m
"""
    
    module_node = parser.parse(source)
    expected_node = nodes.import_from(["."], [nodes.import_alias("message", "m")])
    assert_equal(expected_node, module_node.body[0])


@istest
def can_parse_import_from_in_current_package_and_many_names():
    source = """
from . import message, go
"""
    
    module_node = parser.parse(source)
    expected_node = nodes.import_from(["."], [
        nodes.import_alias("message", None),
        nodes.import_alias("go", None),
    ])
    assert_equal(expected_node, module_node.body[0])


@istest
def can_parse_import_from_with_relative_import_of_child_module():
    source = """
from .x.y import message
"""
    
    module_node = parser.parse(source)
    expected_node = nodes.import_from([".", "x", "y"], [
        nodes.import_alias("message", None),
    ])
    assert_equal(expected_node, module_node.body[0])


@istest
def can_parse_import_from_with_relative_import_of_parent():
    source = """
from ...x.y import message
"""
    
    module_node = parser.parse(source)
    expected_node = nodes.import_from(["..", "..", "x", "y"], [
        nodes.import_alias("message", None),
    ])
    assert_equal(expected_node, module_node.body[0])


@istest
def can_parse_absolute_import_from():
    source = """
from x.y import message
"""
    
    module_node = parser.parse(source)
    expected_node = nodes.import_from(["x", "y"], [
        nodes.import_alias("message", None),
    ])
    assert_equal(expected_node, module_node.body[0])


@istest
def can_parse_import_package():
    source = """
import messages
"""
    
    module_node = parser.parse(source)
    expected_node = nodes.Import([nodes.import_alias("messages", None)])
    assert_equal(expected_node, module_node.body[0])


@istest
def can_parse_function_definition():
    source = """
def f():
    pass
"""
    
    module_node = parser.parse(source)
    assert_equal(nodes.func("f", nodes.args([]), None, []), module_node.body[0])


@istest
def can_parse_argument_and_return_annotations():
    source = """
def f(x: int) -> str:
    pass
"""
    
    module_node = parser.parse(source)
    arg = nodes.arg("x", nodes.ref("int"))
    expected = nodes.func("f", nodes.args([arg]), nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_no_args():
    source = """
#:: -> str
def f():
    pass
"""
    
    module_node = parser.parse(source)
    expected = nodes.func("f", nodes.args([]), nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_no_args_for_function_after_indent():
    source = """
#:: -> str
def f():
    #:: -> int
    def g():
        pass
"""
    
    module_node = parser.parse(source)
    expected = nodes.func("g", nodes.args([]), nodes.ref("int"), [])
    assert_equal(expected, module_node.body[0].body[0])


@istest
def can_parse_signature_comment_with_no_args_for_function_after_dedent():
    source = """
#:: -> str
def f():
    pass
    
#:: -> int
def g():
    pass
"""
    
    module_node = parser.parse(source)
    expected = nodes.func("g", nodes.args([]), nodes.ref("int"), [])
    assert_equal(expected, module_node.body[1])


@istest
def can_parse_signature_comment_with_one_arg():
    source = """
#:: int -> str
def f(x):
    pass
"""
    
    module_node = parser.parse(source)
    arg = nodes.arg("x", nodes.ref("int"))
    expected = nodes.func("f", nodes.args([arg]), nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])



@istest
def can_parse_signature_comment_with_multiple_args():
    source = """
#:: int, str -> str
def f(x, y):
    pass
"""
    
    module_node = parser.parse(source)
    args = nodes.args([
        nodes.arg("x", nodes.ref("int")),
        nodes.arg("y", nodes.ref("str")),
    ])
    expected = nodes.func("f", args, nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_type_application_with_one_generic_parameter():
    source = """
#:: -> list[str]
def f():
    pass
"""
    
    module_node = parser.parse(source)
    return_node = nodes.type_apply(nodes.ref("list"), [nodes.ref("str")])
    expected = nodes.func("f", nodes.args([]), return_node, [])
    assert_equal(expected, module_node.body[0])



@istest
def can_parse_signature_comment_with_type_application_with_many_generic_parameters():
    source = """
#:: -> dict[str, int]
def f():
    pass
"""
    
    module_node = parser.parse(source)
    return_node = nodes.type_apply(nodes.ref("dict"), [nodes.ref("str"), nodes.ref("int")])
    expected = nodes.func("f", nodes.args([]), return_node, [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_one_formal_type_parameter():
    source = """
#:: T => T -> T
def f(x):
    return x
"""
    
    module_node = parser.parse(source)
    expected = nodes.func(
        "f",
        nodes.args([nodes.arg("x", nodes.ref("T"))]),
        nodes.ref("T"),
        [nodes.ret(nodes.ref("x"))],
        ["T"],
    )
    assert_equal(expected, module_node.body[0])


@istest
def error_if_type_signature_has_different_number_of_args_from_def():
    source = """
#:: int, str -> int
def f(x):
    return x
"""
    
    try:
        parser.parse(source)
        assert False, "Expected SyntaxError"
    except SyntaxError as error:
        assert_equal("args length mismatch: def has 1, signature has 2", str(error))



@istest
def test_parse_none():
    _assert_expression_parse(nodes.none(), "None")


@istest
def test_parse_booleans():
    _assert_expression_parse(nodes.boolean(True), "True")
    _assert_expression_parse(nodes.boolean(False), "False")


@istest
def test_parse_int():
    _assert_expression_parse(nodes.int(42), "42")


@istest
def test_parse_string():
    _assert_expression_parse(nodes.string("hello"), "'hello'")


@istest
def test_parse_list():
    _assert_expression_parse(nodes.list([nodes.string("hello"), nodes.int(4)]), "['hello', 4]")


@istest
def test_parse_variable_reference():
    _assert_expression_parse(nodes.ref("x"), "x")


@istest
def test_parse_call():
    expected = nodes.call(
        nodes.ref("f"),
        [nodes.ref("x"), nodes.ref("y")],
    )
    _assert_expression_parse(expected, "f(x, y)")


@istest
def test_attribute_access():
    expected = nodes.attr(nodes.ref("x"), "y")
    _assert_expression_parse(expected, "x.y")


@istest
def test_parse_addition():
    expected = nodes.add(nodes.ref("x"), nodes.ref("y"))
    _assert_expression_parse(expected, "x + y")


@istest
def test_parse_subtraction():
    expected = nodes.sub(nodes.ref("x"), nodes.ref("y"))
    _assert_expression_parse(expected, "x - y")


@istest
def test_parse_multiplication():
    expected = nodes.mul(nodes.ref("x"), nodes.ref("y"))
    _assert_expression_parse(expected, "x * y")


@istest
def test_parse_negation():
    expected = nodes.neg(nodes.ref("x"))
    _assert_expression_parse(expected, "-x")


@istest
def test_parse_subscript():
    expected = nodes.subscript(nodes.ref("x"), nodes.ref("y"))
    _assert_expression_parse(expected, "x[y]")


@istest
def test_parse_expression_statement():
    expected = nodes.expression_statement(nodes.ref("x"))
    _assert_statement_parse(expected, "x")


@istest
def test_parse_return_statement():
    expected = nodes.ret(nodes.ref("x"))
    _assert_statement_parse(expected, "return x")


@istest
def test_parse_single_assignment():
    expected = nodes.assign(["x"], nodes.ref("y"))
    _assert_statement_parse(expected, "x = y")


@istest
def test_parse_multiple_assignments():
    expected = nodes.assign(["x", "y"], nodes.ref("z"))
    _assert_statement_parse(expected, "x = y = z")


@istest
def test_parse_if_statement():
    expected = nodes.if_else(
        nodes.ref("b"),
        [nodes.ret(nodes.ref("x"))],
        [],
    )
    _assert_statement_parse(expected, "if b:\n  return x")


@istest
def test_parse_if_else_statement():
    expected = nodes.if_else(
        nodes.ref("b"),
        [nodes.ret(nodes.ref("x"))],
        [nodes.ret(nodes.ref("y"))],
    )
    _assert_statement_parse(expected, "if b:\n  return x\nelse:\n  return y")


@istest
def test_parse_for_loop():
    expected = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [nodes.ret(nodes.ref("x"))])
    
    _assert_statement_parse(expected, "for x in xs:\n  return x")



def _assert_expression_parse(expected, source):
    module = parser.parse(source)
    assert isinstance(module, nodes.Module)
    
    expression_statement = module.body[0]
    assert isinstance(expression_statement, nodes.ExpressionStatement)
    
    assert_equal(expected, expression_statement.value)


def _assert_statement_parse(expected, source):
    module = parser.parse(source)
    assert isinstance(module, nodes.Module)
    
    assert_equal(expected, module.body[0])
