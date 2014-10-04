from nose.tools import istest, assert_equal, assert_raises_regexp

from nope import parser, nodes
from nope.parser.typing import parse_signature


@istest
def can_parse_signature_with_return_type_and_no_args():
    expected_signature = nodes.signature(returns=nodes.ref("str"))
    assert_equal(expected_signature, parse_signature("-> str"))


@istest
def can_parse_signature_with_one_arg():
    expected_signature = nodes.signature(
        args=[nodes.signature_arg(nodes.ref("int"))],
        returns=nodes.ref("str")
    )
    assert_equal(expected_signature, parse_signature("int -> str"))


@istest
def can_parse_signature_with_multiple_args():
    expected_signature = nodes.signature(
        args=[
            nodes.signature_arg(nodes.ref("int")),
            nodes.signature_arg(nodes.ref("str"))
        ],
        returns=nodes.ref("str")
    )
    assert_equal(expected_signature, parse_signature("int, str -> str"))


@istest
def can_parse_signature_with_named_arg():
    expected_signature = nodes.signature(
        args=[nodes.signature_arg("x", nodes.ref("int"))],
        returns=nodes.ref("str"),
    )
    assert_equal(expected_signature, parse_signature("x: int -> str"))


@istest
def can_parse_signature_comment_with_type_application_with_one_generic_parameter():
    expected_signature = nodes.signature(
        returns=nodes.type_apply(nodes.ref("list"), [nodes.ref("str")])
    )
    assert_equal(expected_signature, parse_signature("-> list[str]"))


@istest
def can_parse_signature_comment_with_type_application_with_many_generic_parameters():
    expected_signature = nodes.signature(
        returns=nodes.type_apply(nodes.ref("dict"), [nodes.ref("str"), nodes.ref("int")]),
    )
    assert_equal(expected_signature, parse_signature("-> dict[str, int]"))


@istest
def can_parse_signature_comment_with_one_formal_type_parameter():
    expected_signature = nodes.signature(
        type_params=["T"],
        args=[nodes.signature_arg(nodes.ref("T"))],
        returns=nodes.ref("T")
    )
    assert_equal(expected_signature, parse_signature("T => T -> T"))