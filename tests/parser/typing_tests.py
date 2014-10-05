from nose.tools import istest, assert_equal, assert_raises_regexp

from nope import parser, nodes
from nope.parser.typing import parse_explicit_type


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
        type_params=["T"],
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
