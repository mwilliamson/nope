import io
import functools

from nose.tools import istest, assert_equal

from nope import nodes
from nope.parser.typing import parse_explicit_type, parse_notes


@istest
def can_parse_reference_to_simple_class():
    assert_equal(nodes.ref("str"), parse_explicit_type("str"))


@istest
def can_parse_signature_with_return_type_and_no_args():
    expected_signature = nodes.signature(returns=nodes.ref("str"))
    assert_equal(expected_signature, parse_explicit_type("-> str"))


@istest
def can_parse_signature_with_one_arg():
    expected_signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("str")
    )
    assert_equal(expected_signature, parse_explicit_type("int -> str"))


@istest
def can_parse_signature_with_multiple_args():
    expected_signature = nodes.signature(
        args=[
            nodes.signature_arg(nodes.ref("int")),
            nodes.signature_arg(nodes.ref("str"))
        ],
        returns=nodes.ref("str")
    )
    assert_equal(expected_signature, parse_explicit_type("int, str -> str"))


@istest
def can_parse_signature_with_named_arg():
    expected_signature = nodes.signature(
        args=[nodes.signature_arg("x", nodes.ref("int"))],
        returns=nodes.ref("str"),
    )
    assert_equal(expected_signature, parse_explicit_type("x: int -> str"))


@istest
def can_parse_signature_with_optional_arg():
    expected_signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"), optional=True)],
        returns=nodes.ref("str")
    )
    assert_equal(expected_signature, parse_explicit_type("?int -> str"))


@istest
def can_parse_explicit_type_with_type_application_with_one_generic_parameter():
    assert_equal(
        nodes.type_apply(nodes.ref("list"), [nodes.ref("str")]),
        parse_explicit_type("list[str]")
    )


@istest
def can_parse_signature_comment_with_type_application_with_one_generic_parameter():
    expected_signature = nodes.signature(
        returns=nodes.type_apply(nodes.ref("list"), [nodes.ref("str")])
    )
    assert_equal(expected_signature, parse_explicit_type("-> list[str]"))


@istest
def can_parse_signature_comment_with_type_application_with_many_generic_parameters():
    expected_signature = nodes.signature(
        returns=nodes.type_apply(nodes.ref("dict"), [nodes.ref("str"), nodes.ref("int")]),
    )
    assert_equal(expected_signature, parse_explicit_type("-> dict[str, int]"))


@istest
def can_parse_signature_comment_with_one_formal_type_parameter():
    expected_signature = nodes.signature(
        type_params=[nodes.formal_type_parameter("T")],
        args=[nodes.signature_arg(nodes.ref("T"))],
        returns=nodes.ref("T")
    )
    assert_equal(expected_signature, parse_explicit_type("T => T -> T"))


@istest
def can_parse_signature_with_function_type_as_argument():
    sub_signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("str")
    )
    expected_signature = nodes.signature(
        args=[
            nodes.signature_arg(sub_signature)
        ],
        returns=nodes.ref("none")
    )
    assert_equal(expected_signature, parse_explicit_type("(int -> str) -> none"))


@istest
def can_parse_type_union():
    assert_equal(
        nodes.type_union([nodes.ref("none"), nodes.ref("str"), nodes.ref("int")]),
        parse_explicit_type("none | str | int")
    )


@istest
def test_types_can_be_defined_with_type_statement():
    source = """
#:type Identifier = int | str
x = 1
"""
    expected_node = nodes.TypeDefinition(
        "Identifier",
        nodes.type_union([nodes.ref("int"), nodes.ref("str")])
    )
    
    note = _parse_type_definition_note(source)
    assert_equal(expected_node, note)


@istest
def type_definitions_can_span_multiple_lines():
    source = """
#:type Identifier =
#:   int
#: | str
x = 1
"""
    expected_node = nodes.TypeDefinition(
        "Identifier",
        nodes.type_union([nodes.ref("int"), nodes.ref("str")])
    )
    
    note = _parse_type_definition_note(source)
    assert_equal(expected_node, note)


@istest
def generic_specifiers_use_generic_keyword():
    source = """
#:generic T
class A:
    pass
"""
    note = _parse_generic_note(source)
    assert_equal([nodes.formal_type_parameter("T")], note)


@istest
def generic_specifiers_can_define_multiple_formal_type_parameters():
    source = """
#:generic T1, T2, R
class A:
    pass
"""
    note = _parse_generic_note(source)
    expected = [
        nodes.formal_type_parameter("T1"),
        nodes.formal_type_parameter("T2"),
        nodes.formal_type_parameter("R"),
    ]
    assert_equal(expected, note)


def _parse_note_of_type(note_type, source):
    note, = getattr(parse_notes(io.StringIO(source)), note_type).values()
    return note[1]

_parse_type_definition_note = functools.partial(_parse_note_of_type, "type_definitions")
_parse_generic_note = functools.partial(_parse_note_of_type, "generics")
