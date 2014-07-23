from nose.tools import istest, assert_equal

from nope import js


@istest
def test_serialize_null():
    assert_equal("null", js.dumps(js.null))
    

@istest
def test_serialize_number():
    assert_equal("42", js.dumps(js.number(42)))


@istest
def test_serialize_string():
    assert_equal('"hello"', js.dumps(js.string("hello")))


@istest
def test_serialize_variable_reference():
    assert_equal("flynn", js.dumps(js.ref("flynn")))


@istest
def test_serialize_call_with_no_args():
    assert_equal("f(x)", js.dumps(js.call(js.ref("f"), [])))
    

@istest
def test_serialize_call_with_one_arg():
    assert_equal("f(x)", js.dumps(js.call(js.ref("f"), [js.ref("x")])))


@istest
def test_serialize_call_with_no_args():
    assert_equal("f(x, y)", js.dumps(js.call(js.ref("f"), [js.ref("x"), js.ref("y")])))


@istest
def test_serialize_expression_statement():
    assert_equal("x;", js.dumps(js.expression_statement(js.ref("x"))))


@istest
def test_serialize_function_declaration():
    func = js.function_declaration(
        name="f",
        args=["x", "y"],
        body = [
            js.expression_statement(js.ref("y")),
            js.expression_statement(js.ref("x")),
        ],
    )
    assert_equal("function f(x, y) { y;x; }", js.dumps(func))


@istest
def test_serialize_return_statement():
    func = js.ret(js.ref("x"))
    assert_equal("return x;", js.dumps(func))


@istest
def test_serialize_statements():
    assert_equal("x;y;", js.dumps(js.statements([
        js.expression_statement(js.ref("x")),
        js.expression_statement(js.ref("y")),
    ])))
