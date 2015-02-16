import collections

from nose.tools import istest, assert_equal

from nope.platforms.nodejs import js


@istest
def test_serialize_null():
    assert_equal("null", _dumps(js.null))


@istest
def test_serialize_booleans():
    assert_equal("true", _dumps(js.boolean(True)))
    assert_equal("false", _dumps(js.boolean(False)))
    

@istest
def test_serialize_number():
    assert_equal("42", _dumps(js.number(42)))


@istest
def test_serialize_string():
    assert_equal('"hello"', _dumps(js.string("hello")))


@istest
def test_serialize_variable_reference():
    assert_equal("flynn", _dumps(js.ref("flynn")))


@istest
def test_serialize_array():
    assert_equal("[1, null]", _dumps(js.array([js.number(1), js.null])))


@istest
def test_serialize_object():
    obj = js.obj(collections.OrderedDict([("a", js.number(1)), ("b", js.number(2))]))
    assert_equal('{"a": 1, "b": 2}', _dumps(obj))


@istest
def test_serialize_call_with_no_args():
    assert_equal("f()", _dumps(js.call(js.ref("f"), [])))
    

@istest
def test_serialize_call_with_one_arg():
    assert_equal("f(x)", _dumps(js.call(js.ref("f"), [js.ref("x")])))


@istest
def test_serialize_call_with_multiple_args():
    assert_equal("f(x, y)", _dumps(js.call(js.ref("f"), [js.ref("x"), js.ref("y")])))


@istest
def test_serialize_property_access_with_dot_notation():
    assert_equal("(x).y", _dumps(js.property_access(js.ref("x"), "y")))


@istest
def test_serialize_property_access_with_subscript_notation():
    assert_equal("(x)[y]", _dumps(js.property_access(js.ref("x"), js.ref("y"))))
    

@istest
def test_serialize_binary_operation():
    assert_equal("(x) + (y)", _dumps(js.binary_operation("+", js.ref("x"), js.ref("y"))))
    

@istest
def test_serialize_unary_operation():
    assert_equal("-(x)", _dumps(js.unary_operation("-", js.ref("x"))))


@istest
def test_serialize_assignment():
    assignment = js.assign("x", js.ref("y"))
    assert_equal("x = y", _dumps(assignment))


@istest
def test_serialize_expression_statement():
    assert_equal("x;", _dumps(js.expression_statement(js.ref("x"))))


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
    assert_equal("function f(x, y) { y;x; }", _dumps(func))


@istest
def test_serialize_function_expression():
    func = js.function_expression(
        args=["x", "y"],
        body = [
            js.expression_statement(js.ref("y")),
            js.expression_statement(js.ref("x")),
        ],
    )
    assert_equal("function(x, y) { y;x; }", _dumps(func))


@istest
def test_serialize_return_statement():
    statement = js.ret(js.ref("x"))
    assert_equal("return x;", _dumps(statement))


@istest
def test_serialize_var_declaration():
    statement = js.var("x")
    assert_equal("var x;", _dumps(statement))


@istest
def test_serialize_var_declaration_with_immediate_assignment():
    statement = js.var("x", js.ref("y"))
    assert_equal("var x = y;", _dumps(statement))


@istest
def test_serialize_if():
    if_else = js.if_else(
        js.ref("x"),
        [js.ret(js.ref("y"))],
        [],
    )
    assert_equal("if (x) { return y; }", _dumps(if_else))


@istest
def test_serialize_if_else():
    if_else = js.if_else(
        js.ref("x"),
        [js.ret(js.ref("y"))],
        [js.ret(js.ref("z"))],
    )
    assert_equal("if (x) { return y; } else { return z; }", _dumps(if_else))


@istest
def test_serialize_statements():
    assert_equal("x;y;", _dumps(js.statements([
        js.expression_statement(js.ref("x")),
        js.expression_statement(js.ref("y")),
    ])))


@istest
def test_serialize_try_catch():
    node = js.try_catch(
        [js.ret(js.ref("x"))],
        "error",
        [js.ret(js.ref("y"))]
    )
    assert_equal("try { return x; } catch (error) { return y; }", _dumps(node))


@istest
def test_serialize_try_finally():
    node = js.try_catch(
        [js.ret(js.ref("x"))],
        finally_body=[js.ret(js.ref("z"))],
    )
    assert_equal("try { return x; } finally { return z; }", _dumps(node))


@istest
def test_serialize_try_catch_finally():
    node = js.try_catch(
        [js.ret(js.ref("x"))],
        "error",
        [js.ret(js.ref("y"))],
        [js.ret(js.ref("z"))],
    )
    assert_equal("try { return x; } catch (error) { return y; } finally { return z; }", _dumps(node))


@istest
def test_serialize_while_loop():
    node = js.while_loop(
        js.ref("condition"),
        [js.ret(js.ref("value"))]
    )
    assert_equal("while (condition) { return value; }", _dumps(node))


@istest
def test_serialize_break():
    node = js.break_statement()
    assert_equal("break;", _dumps(node))


@istest
def test_serialize_continue():
    node = js.continue_statement()
    assert_equal("continue;", _dumps(node))


@istest
def test_serialize_throw():
    node = js.throw(js.ref("error"))
    assert_equal("throw error;", _dumps(node))


def _dumps(node):
    return js.dumps(node, pretty_print=False)


@istest
class PrettyPrintTests(object):
    @istest
    def statements_are_separated_by_new_lines(self):
        statements = js.statements([
            js.expression_statement(js.ref("y")),
            js.expression_statement(js.ref("x")),
        ])
        assert_equal("y;\nx;\n", self._dumps(statements))


    @istest
    def bodies_of_blocks_are_indented(self):
        node = js.while_loop(
            js.ref("condition"),
            [
                js.expression_statement(js.ref("y")),
                js.expression_statement(js.ref("x")),
            ]
        )
        assert_equal("while (condition) {\n    y;\n    x;\n}\n", self._dumps(node))
    
    def _dumps(self, node):
        return js.dumps(node, pretty_print=True)
