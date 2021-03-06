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
    def uses_parens_to_surround_arguments(self):
        node = cs.new(cs.ref("A"), [cs.ref("x"), cs.ref("y")])
        assert_equal("new A(x, y)", cs.dumps(node))
        
    @istest
    def uses_braced_list_for_member_setters(self):
        node = cs.new(cs.ref("A"), [], [("X", cs.ref("x")), ("Y", cs.ref("y"))])
        expected = """new A {
    X = x,
    Y = y,
}"""
        assert_equal(expected, cs.dumps(node))


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


@istest
class ClassTests(object):
    @istest
    def class_has_internal_visibility(self):
        node = cs.class_("A", [])
        expected = """internal class A {
}
"""
        assert_equal(expected, cs.dumps(node))
    
    @istest
    def class_body_is_written_out(self):
        node = cs.class_("A", [cs.method("Main", [], [])])
        expected = """internal class A {
    internal dynamic Main() {
    }
}
"""
        assert_equal(expected, cs.dumps(node))


@istest
class FieldTests(object):
    @istest
    def field_is_internal_and_dynamic(self):
        node = cs.field("X")
        expected = """internal dynamic X;
"""
        assert_equal(expected, cs.dumps(node))

@istest
class MethodTests(object):
    @istest
    def method_has_internal_visibility(self):
        node = cs.method("f", [], [])
        expected = """internal dynamic f() {
}
"""
        assert_equal(expected, cs.dumps(node))
    
    @istest
    def method_has_dynamic_arguments(self):
        node = cs.method("f", [cs.arg("x"), cs.arg("y")], [])
        expected = """internal dynamic f(dynamic x, dynamic y) {
}
"""
        assert_equal(expected, cs.dumps(node))
    
    @istest
    def method_return_type_can_be_overridden(self):
        node = cs.method("f", [], [], returns=cs.void)
        expected = """internal void f() {
}
"""
        assert_equal(expected, cs.dumps(node))
    
    @istest
    def method_has_body(self):
        node = cs.method("f", [], [cs.ret(cs.ref("x"))])
        expected = """internal dynamic f() {
    return x;
}
"""
        assert_equal(expected, cs.dumps(node))
    
    @istest
    def method_can_be_set_as_ststic(self):
        node = cs.method("f", [], [], static=True)
        expected = """internal static dynamic f() {
}
"""
        assert_equal(expected, cs.dumps(node))
