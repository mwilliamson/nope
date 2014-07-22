from nose.tools import istest, assert_equal

from nope import js


@istest
def test_serialize_number():
    assert_equal("42", js.dumps(js.number(42)))


@istest
def test_serialize_variable_reference():
    assert_equal("flynn", js.dumps(js.ref("flynn")))


@istest
def test_serialize_call_with_one_arg():
    assert_equal("f(x)", js.dumps(js.call(js.ref("f"), [js.ref("x")])))


@istest
def test_serialize_expression_statement():
    assert_equal("x;", js.dumps(js.expression_statement(js.ref("x"))))


@istest
def test_serialize_statements():
    assert_equal("x;y;", js.dumps(js.statements([
        js.expression_statement(js.ref("x")),
        js.expression_statement(js.ref("y")),
    ])))
