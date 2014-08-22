from nose.tools import istest, assert_equal, assert_raises_regexp

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
def function_can_have_no_signature_if_it_takes_no_args():
    source = """
def f():
    pass
"""
    
    module_node = parser.parse(source)
    expected = nodes.func("f", nodes.signature(), nodes.args([]), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_return_type_and_no_args():
    source = """
#:: -> str
def f():
    pass
"""
    
    module_node = parser.parse(source)
    signature = nodes.signature(returns=nodes.ref("str"))
    expected = nodes.func("f", signature, nodes.args([]), [])
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
    signature = nodes.signature(returns=nodes.ref("int"))
    expected = nodes.func("g", signature, nodes.args([]), [])
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
    signature = nodes.signature(returns=nodes.ref("int"))
    expected = nodes.func("g", signature, nodes.args([]), [])
    assert_equal(expected, module_node.body[1])


@istest
def can_parse_signature_comment_with_one_arg():
    source = """
#:: int -> str
def f(x):
    pass
"""
    
    module_node = parser.parse(source)
    signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("str")
    )
    expected = nodes.func("f", signature, nodes.args([nodes.arg("x")]), [])
    assert_equal(expected, module_node.body[0])



@istest
def can_parse_signature_comment_with_multiple_args():
    source = """
#:: int, str -> str
def f(x, y):
    pass
"""
    
    module_node = parser.parse(source)
    signature = nodes.signature(
        args=[
            nodes.signature_arg(nodes.ref("int")),
            nodes.signature_arg(nodes.ref("str"))
        ],
        returns=nodes.ref("str")
    )
    args = nodes.args([
        nodes.arg("x"),
        nodes.arg("y"),
    ])
    expected = nodes.func("f", signature, args, [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_named_arg():
    source = """
#:: x: int -> str
def f(x):
    pass
"""
    
    module_node = parser.parse(source)
    signature = nodes.signature(
        args=[nodes.signature_arg("x", nodes.ref("int"))],
        returns=nodes.ref("str"),
    )
    expected = nodes.func("f", signature, nodes.args([nodes.arg("x")]), [])
    assert_equal(expected, module_node.body[0])


@istest
def syntax_error_if_name_of_argument_does_not_match_name_in_signature():
    source = """
#:: y: int -> str
def f(x):
    pass
"""
    
    try:
        module_node = parser.parse(source)
        assert False, "Expected SyntaxError"
    except SyntaxError as error:
        assert_equal("argument 'x' has name 'y' in signature", str(error))


@istest
def can_parse_signature_comment_with_type_application_with_one_generic_parameter():
    source = """
#:: -> list[str]
def f():
    pass
"""
    
    module_node = parser.parse(source)
    signature = nodes.signature(
        returns=nodes.type_apply(nodes.ref("list"), [nodes.ref("str")])
    )
    expected = nodes.func("f", signature, nodes.args([]), [])
    assert_equal(expected, module_node.body[0])



@istest
def can_parse_signature_comment_with_type_application_with_many_generic_parameters():
    source = """
#:: -> dict[str, int]
def f():
    pass
"""
    
    module_node = parser.parse(source)
    signature = nodes.signature(
        returns=nodes.type_apply(nodes.ref("dict"), [nodes.ref("str"), nodes.ref("int")]),
    )
    expected = nodes.func("f", signature, nodes.args([]), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_one_formal_type_parameter():
    source = """
#:: T => T -> T
def f(x):
    return x
"""
    
    module_node = parser.parse(source)
    signature = nodes.signature(
        type_params=["T"],
        args=[nodes.signature_arg(nodes.ref("T"))],
        returns=nodes.ref("T")
    )
    expected = nodes.func(
        "f",
        signature,
        nodes.args([nodes.arg("x")]),
        [nodes.ret(nodes.ref("x"))],
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
def test_parse_return_with_no_value_is_parsed_as_return_none():
    expected = nodes.ret(nodes.none())
    _assert_statement_parse(expected, "return")


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
def test_parse_while_loop():
    expected = nodes.while_loop(nodes.ref("x"), [nodes.ret(nodes.ref("x"))])
    
    _assert_statement_parse(expected, "while x:\n  return x")


@istest
def test_parse_while_loop_with_else_body():
    expected = nodes.while_loop(nodes.ref("x"), [], [nodes.ret(nodes.ref("x"))])
    
    _assert_statement_parse(expected, "while x:\n  pass\nelse:\n  return x")


@istest
def test_parse_for_loop():
    expected = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [nodes.ret(nodes.ref("x"))])
    
    _assert_statement_parse(expected, "for x in xs:\n  return x")


@istest
def test_parse_for_loop_with_else_body():
    expected = nodes.for_loop(
        nodes.ref("x"), nodes.ref("xs"),
        [],
        [nodes.ret(nodes.ref("x"))],
    )
    
    _assert_statement_parse(expected, "for x in xs:\n  pass\nelse:\n  return x")


@istest
def test_parse_break():
    _assert_statement_parse(nodes.break_statement(), "break")


@istest
def test_parse_continue():
    _assert_statement_parse(nodes.continue_statement(), "continue")


@istest
def test_parse_try_finally():
    expected = nodes.try_statement(
        [nodes.expression_statement(nodes.ref("x"))],
        finally_body=[nodes.expression_statement(nodes.ref("y"))],
    )
    
    _assert_statement_parse(expected, "try:\n  x\nfinally:\n  y")


@istest
def test_parse_try_except_that_catches_all_exceptions():
    expected = nodes.try_statement(
        [nodes.expression_statement(nodes.ref("x"))],
        handlers=[
            nodes.except_handler(None, None, [
                nodes.expression_statement(nodes.ref("y"))
            ]),
        ]
    )
    
    _assert_statement_parse(expected, "try:\n  x\nexcept:\n  y")


@istest
def test_parse_try_except_with_specific_type():
    expected = nodes.try_statement(
        [nodes.expression_statement(nodes.ref("x"))],
        handlers=[
            nodes.except_handler(nodes.ref("AssertionError"), None, [
                nodes.expression_statement(nodes.ref("y"))
            ]),
        ]
    )
    
    _assert_statement_parse(expected, "try:\n  x\nexcept AssertionError:\n  y")


@istest
def test_parse_try_except_with_specific_type_and_identifier():
    expected = nodes.try_statement(
        [nodes.expression_statement(nodes.ref("x"))],
        handlers=[
            nodes.except_handler(nodes.ref("AssertionError"), "error", [
                nodes.expression_statement(nodes.ref("y"))
            ]),
        ]
    )
    
    _assert_statement_parse(expected, "try:\n  x\nexcept AssertionError as error:\n  y")


@istest
def test_parse_raise():
    _assert_statement_parse(nodes.raise_statement(nodes.ref("x")), "raise x")


@istest
def test_parse_assert_simple_form():
    _assert_statement_parse(nodes.assert_statement(nodes.ref("x")), "assert x")


@istest
def test_parse_assert_extended_form():
    _assert_statement_parse(
        nodes.assert_statement(nodes.ref("x"), nodes.string("Oops")),
        "assert x, 'Oops'"
    )


@istest
def test_parse_with_statement_single_context_manager_no_target():
    expected_node = nodes.with_statement(
        nodes.ref("x"),
        None,
        [nodes.ret(nodes.ref("y"))],
    )
    _assert_statement_parse(expected_node, "with x:\n  return y")


@istest
def test_parse_with_statement_single_context_manager_with_target():
    expected_node = nodes.with_statement(
        nodes.ref("x"),
        nodes.ref("x2"),
        [nodes.ret(nodes.ref("y"))],
    )
    _assert_statement_parse(expected_node, "with x as x2:\n  return y")


@istest
def test_parse_with_statement_with_multiple_context_managers():
    expected_node = nodes.with_statement(
        nodes.ref("x"),
        nodes.ref("x2"),
        [
            nodes.with_statement(
                nodes.ref("y"),
                None,
                [nodes.ret(nodes.ref("z"))],
            )
        ]
    )
    _assert_statement_parse(expected_node, "with x as x2, y:\n    return z")



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
