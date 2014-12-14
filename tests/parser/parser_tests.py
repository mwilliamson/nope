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
def known_future_import_is_ignored():
    # As of Python 3.4, all valid future imports are mandatory
    source = """#!/usr/bin/env python
from __future__ import unicode_literals
"""
    
    module_node = parser.parse(source)
    assert_equal([], module_node.body)


@istest
def unknown_future_import_is_parser_error():
    source = """#!/usr/bin/env python
from __future__ import blah
"""
    
    try:
        parser.parse(source)
        assert False
    except SyntaxError as error:
        assert_equal("Unknown __future__ import: 'blah'", error.msg)


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
    expected = nodes.func("f", nodes.args([]), [])
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
    expected = nodes.typed(signature, nodes.func("g", nodes.args([]), []))
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
    expected = nodes.typed(signature, nodes.func("g", nodes.args([]), []))
    assert_equal(expected, module_node.body[1])


@istest
class OptionalArgumentTests(object):
    @istest
    def optional_arg_can_have_default_value_of_none(self):
        source = """
#:: ?str -> str
def f(x=None):
    pass
"""
        
        module_node = parser.parse(source)
        expected = nodes.args([nodes.arg("x", optional=True)])
        assert_equal(expected, module_node.body[0].args)


    @istest
    def default_argument_cannot_be_expression_other_than_none(self):
        source = """
#:: ?str -> str
def f(x=1):
    pass
"""
        _assert_syntax_error("default argument must be None", source)


    @istest
    def can_have_required_arguments_before_optional_arguments(self):
        source = """
#:: str, str, ?str, ?str -> str
def f(a, b, c=None, d=None):
    pass
"""
        
        module_node = parser.parse(source)
        expected = nodes.args([
            nodes.arg("a"),
            nodes.arg("b"),
            nodes.arg("c", optional=True),
            nodes.arg("d", optional=True),
        ])
        assert_equal(expected, module_node.body[0].args)


@istest
def function_decorators_are_not_supported():
    source = """
#:: -> str
@test
def f():
    pass
"""
    _assert_syntax_error("function decorators are not supported", source)


@istest
def keyword_only_arguments_are_not_supported():
    source = """
#:: -> str
def f(*, x):
    pass
"""
    _assert_syntax_error("keyword-only arguments are not supported", source)


@istest
def var_args_are_not_supported():
    source = """
#:: -> str
def f(*args):
    pass
"""
    _assert_syntax_error("arguments in the form '*args' are not supported", source)


@istest
def keyword_var_args_are_not_supported():
    source = """
#:: -> str
def f(**kwargs):
    pass
"""
    _assert_syntax_error("arguments in the form '**kwargs' are not supported", source)


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
def test_parse_tuple_literal():
    _assert_expression_parse(
        nodes.tuple_literal([nodes.string("hello"), nodes.int(4)]),
        "('hello', 4)"
    )


@istest
def test_parse_list_literal():
    _assert_expression_parse(nodes.list_literal([nodes.string("hello"), nodes.int(4)]), "['hello', 4]")


@istest
def test_parse_dict_literal():
    _assert_expression_parse(
        nodes.dict_literal([
            (nodes.string("hello"), nodes.int(4)),
            (nodes.string("there"), nodes.int(5)),
        ]),
        "{'hello': 4, 'there': 5}"
    )


@istest
def test_parse_variable_reference():
    _assert_expression_parse(nodes.ref("x"), "x")


@istest
def test_parse_call_with_positional_arguments():
    expected = nodes.call(
        nodes.ref("f"),
        [nodes.ref("x"), nodes.ref("y")],
    )
    _assert_expression_parse(expected, "f(x, y)")


@istest
def test_parse_call_with_keyword_arguments():
    expected = nodes.call(
        nodes.ref("f"),
        [],
        {"person": nodes.ref("bob"), "hat": nodes.ref("fedora")},
    )
    _assert_expression_parse(expected, "f(person=bob, hat=fedora)")


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
def test_parse_in_operator():
    expected = nodes.contains(nodes.ref("y"), nodes.ref("x"))
    _assert_expression_parse(expected, "x in y")


@istest
def test_parse_subscript_with_index():
    expected = nodes.subscript(nodes.ref("x"), nodes.ref("y"))
    _assert_expression_parse(expected, "x[y]")


@istest
def test_parse_subscript_with_slice():
    expected = nodes.subscript(
        nodes.ref("x"),
        nodes.slice(nodes.ref("a"), nodes.ref("b"), nodes.ref("c")),
    )
    _assert_expression_parse(expected, "x[a:b:c]")


@istest
def test_missing_subscript_slice_values_are_treated_as_none():
    expected = nodes.subscript(nodes.ref("x"), nodes.slice(nodes.none(), nodes.none(), nodes.none()))
    _assert_expression_parse(expected, "x[:]")


@istest
def test_parse_single_comparison():
    x = nodes.ref("x")
    y = nodes.ref("y")
    _assert_expression_parse(nodes.eq(x, y), "x == y")
    _assert_expression_parse(nodes.ne(x, y), "x != y")
    _assert_expression_parse(nodes.lt(x, y), "x < y")
    _assert_expression_parse(nodes.le(x, y), "x <= y")
    _assert_expression_parse(nodes.gt(x, y), "x > y")
    _assert_expression_parse(nodes.ge(x, y), "x >= y")


@istest
def test_parse_compound_comparisons():
    _assert_expression_parse(
        _parse_expression("x < y and y < z"),
        "x < y < z"
    )


@istest
def test_parse_simple_boolean_operators():
    x = nodes.ref("x")
    y = nodes.ref("y")
    _assert_expression_parse(nodes.bool_and(x, y), "x and y")
    _assert_expression_parse(nodes.bool_or(x, y), "x or y")
    _assert_expression_parse(nodes.bool_not(x), "not x")


@istest
def test_parse_chained_boolean_operators():
    _assert_expression_parse(
        nodes.bool_and(
            nodes.bool_and(nodes.ref("a"), nodes.ref("b")),
            nodes.ref("c"),
        ),
        "a and b and c"
    )


@istest
def test_parse_is_operation():
    _assert_expression_parse(nodes.is_(nodes.ref("x"), nodes.ref("y")), "x is y")


@istest
def test_parse_single_list_comprehension():
    _assert_expression_parse(
        nodes.list_comprehension(
            nodes.call(nodes.ref("f"), [nodes.ref("x")]),
            nodes.comprehension(nodes.ref("x"), nodes.ref("xs"))
        ),
        "[f(x) for x in xs]"
    )


@istest
def test_parse_generator_expression():
    _assert_expression_parse(
        nodes.generator_expression(
            nodes.call(nodes.ref("f"), [nodes.ref("x")]),
            nodes.comprehension(nodes.ref("x"), nodes.ref("xs"))
        ),
        "(f(x) for x in xs)"
    )


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
def test_error_if_trying_to_parse_try_statement_with_else_block():
    _assert_syntax_error(
        "'else' clause in 'try' statement is unsupported",
        "try:\n  pass\nexcept AssertionError as error:\n  pass\nelse:\n  pass"
    )


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


@istest
def custom_syntax_errors_have_position():
    source = """
class(**bases):
    pass
"""
    try:
        parser.parse(source, filename="breathing-underwater.py")
        assert False, "Expected SyntaxError"
    except SyntaxError as error:
        assert_equal("breathing-underwater.py", error.filename)
        assert_equal(2, error.lineno)
        assert_equal(6, error.offset)


@istest
def nodes_have_position():
    node = _parse_expression("\nNone", filename="take-it-easy.py")
    
    assert_equal("take-it-easy.py", node.location.filename)
    assert_equal(2, node.location.lineno)
    assert_equal(0, node.location.offset)


@istest
def test_parse_empty_class():
    expected_node = nodes.class_def("User", [])
    _assert_statement_parse(expected_node, "class User:\n  pass")


@istest
def test_parse_class_with_body():
    expected_node = nodes.class_def("User", [nodes.assign([nodes.ref("x")], nodes.int(1))])
    _assert_statement_parse(expected_node, "class User:\n  x = 1")


@istest
def test_parse_class_with_base_classes():
    expected_node = nodes.class_def("User", [], base_classes=[nodes.ref("Person")])
    _assert_statement_parse(expected_node, "class User(Person):\n  pass")


@istest
def test_parse_class_with_generics():
    expected_node = nodes.class_def("Option", [], type_params=["T"])
    _assert_statement_parse(expected_node, "#:generic T\nclass Option:\n  pass")


@istest
def test_error_when_class_body_is_not_assignment_nor_function_definition():
    _assert_syntax_error(
        "IfElse node is not supported in current context",
        "class User:\n  if x:\n    y = 1\n  else:\n    y = 2"
    )


@istest
def test_error_when_parsing_class_vararg_base_classes():
    _assert_syntax_error("base classes in the form '*bases' are not supported", "class User(*bases):\n  pass")


@istest
def test_error_when_parsing_class_keywords():
    _assert_syntax_error("class keyword arguments are not supported", "class User(metaclass=Person):\n  pass")


@istest
def test_error_when_parsing_class_kwargs():
    _assert_syntax_error("class keyword arguments are not supported", "class User(**kwargs):\n  pass")


@istest
def test_error_when_parsing_class_decorators():
    _assert_syntax_error("class decorators are not supported", "@wraps\nclass User:\n  pass")


@istest
def test_error_if_signature_is_not_consumed():
    source = """
#:: int -> int
"""
    try:
        parser.parse(source)
        assert False, "Expected SyntaxError"
    except SyntaxError as error:
        assert_equal("explicit type is not valid here", error.msg)
        assert_equal(2, error.lineno)
        assert_equal(0, error.offset)


@istest
def test_type_definitions_can_appear_between_statements():
    source = """
#:type Identifier = int | str
Identifier = None
"""
    module_node = parser.parse(source)
    expected_node = nodes.TypeDefinition(
        "Identifier",
        nodes.type_union([nodes.ref("int"), nodes.ref("str")])
    )
    assert_equal(expected_node, module_node.body[0])
    assert_equal(1, len(module_node.body))


def _assert_expression_parse(expected, source):
    assert_equal(expected, _parse_expression(source))


def _parse_expression(source, filename=None):
    module = parser.parse(source, filename=filename)
    assert isinstance(module, nodes.Module)
    
    expression_statement = module.body[0]
    assert isinstance(expression_statement, nodes.ExpressionStatement)
    
    return expression_statement.value


def _assert_statement_parse(expected, source):
    module = parser.parse(source)
    assert isinstance(module, nodes.Module)
    
    assert_equal(expected, module.body[0])


def _assert_syntax_error(description, source):
    try:
        parser.parse(source)
        assert False, "Expected SyntaxError"
    except SyntaxError as error:
        assert_equal(description, error.msg)
