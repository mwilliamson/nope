import collections

from nose.tools import istest, assert_equal

from nope.platforms.dotnet import cs


@istest
class TryStatementsTests(object):
    @istest
    def test_serialize_try_with_finally_body(self):
        node = cs.try_(
            [cs.ret(cs.ref("x"))],
            finally_body=[cs.expression_statement(cs.ref("y"))],
        )
        expected = """try {
    return x;
} finally {
    y;
}
"""
        assert_equal(expected, cs.dumps(node))


    @istest
    def test_serialize_try_with_unfiltered_catch(self):
        node = cs.try_(
            [cs.ret(cs.ref("x"))],
            handlers=[cs.catch(None, None, [cs.expression_statement(cs.ref("y"))])],
        )
        expected = """try {
    return x;
} catch {
    y;
}
"""
        assert_equal(expected, cs.dumps(node))


    @istest
    def test_serialize_try_with_filtered_catch_without_name(self):
        node = cs.try_(
            [cs.ret(cs.ref("x"))],
            handlers=[cs.catch(cs.ref("Exception"), None, [cs.expression_statement(cs.ref("y"))])],
        )
        expected = """try {
    return x;
} catch (Exception) {
    y;
}
"""
        assert_equal(expected, cs.dumps(node))


    @istest
    def test_serialize_try_with_filtered_catch_with_name(self):
        node = cs.try_(
            [cs.ret(cs.ref("x"))],
            handlers=[cs.catch(cs.ref("Exception"), "exception", [cs.expression_statement(cs.ref("y"))])],
        )
        expected = """try {
    return x;
} catch (Exception exception) {
    y;
}
"""
        assert_equal(expected, cs.dumps(node))


@istest
class VariableDeclarationTests(object):
    @istest
    def variable_without_initial_value_is_declared_as_dynamic(self):
        node = cs.declare("x", None)
        expected = """dynamic x;\n"""
        assert_equal(expected, cs.dumps(node))
    
    @istest
    def variable_with_initial_value_is_declared_as_dynamic_with_initial_value(self):
        node = cs.declare("x", cs.null)
        expected = """dynamic x = null;\n"""
        assert_equal(expected, cs.dumps(node))


@istest
class LambdaTests(object):
    @istest
    def lambda_without_arguments_has_body_serialized(self):
        node = cs.lambda_([], [cs.ret(cs.ref("x"))])
        expected = """(() =>
{
    return x;
})"""
        assert_equal(expected, cs.dumps(node))
    
    
    @istest
    def arguments_have_dynamic_type(self):
        node = cs.lambda_([cs.arg("x")], [])
        expected = """((dynamic x) =>
{
})"""
        assert_equal(expected, cs.dumps(node))
    
    
    @istest
    def arguments_are_separated_by_commas(self):
        node = cs.lambda_([cs.arg("x"), cs.arg("y")], [])
        expected = """((dynamic x, dynamic y) =>
{
})"""
        assert_equal(expected, cs.dumps(node))
        

@istest
class NewTests(object):
    @istest
    def calls_reference_with_new_keyword(self):
        node = cs.new(cs.ref("A"), [])
        assert_equal("new A()", cs.dumps(node))
        
    @istest
    def calls_reference_with_arguments(self):
        node = cs.new(cs.ref("A"), [cs.ref("x"), cs.ref("y")])
        assert_equal("new A(x, y)", cs.dumps(node))


@istest
class AnonymousObjectTests(object):
    @istest
    def object_is_created_with_new_keyword(self):
        node = cs.obj([])
        expected = """new
{
}"""
        assert_equal(expected, cs.dumps(node))
        
    @istest
    def object_members_are_assigned_with_equals_sign(self):
        node = cs.obj([("X", cs.ref("x")), ("Y", cs.ref("y"))])
        expected = """new
{
    X = x,
    Y = y,
}"""
        assert_equal(expected, cs.dumps(node))
