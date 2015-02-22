import os

from nose.tools import istest, assert_equal

from nope import couscous as cc
from nope.platforms.dotnet import cs
from nope.platforms.dotnet.codegeneration import _transform as transform


@istest
class FunctionDefinitionTests(object):
    @istest
    def function_with_zero_arguments_is_converted_to_csharp_lambda_assignment(self):
        node = cc.func("f", [], [cc.ret(cc.none)])
        
        expected = """
f = ((System.Func<dynamic>)(() =>
{
    return __NopeNone.Value;
}));"""
        assert_equal(expected.strip(), cs.dumps(transform(node)).strip())
        
    @istest
    def function_with_multiple_arguments_is_converted_to_csharp_lambda_assignment_with_dynamic_args(self):
        node = cc.func("f", [cc.arg("x"), cc.arg("y")], [cc.ret(cc.none)])
        
        expected = """
f = ((System.Func<dynamic, dynamic, dynamic>)((dynamic x, dynamic y) =>
{
    return __NopeNone.Value;
}));"""
        assert_equal(expected.strip(), cs.dumps(transform(node)).strip())


@istest
class RaiseStatementTests(object):
    @istest
    def raise_generates_throw_with_nope_exception_contained_in_csharp_exception(self):
        node = cc.raise_(cc.ref("x"))
        
        expected = """throw __Nope.Internals.@CreateException(x);
"""
        assert_equal(expected, cs.dumps(transform(node)))


@istest
class TryStatementTests(object):
    @istest
    def try_with_finally_is_converted_to_try_with_finally(self):
        node = cc.try_(
            [cc.ret(cc.ref("x"))],
            finally_body=[cc.expression_statement(cc.ref("y"))]
        )
        
        expected = """try {
    return x;
} finally {
    y;
}
"""
        assert_equal(expected, cs.dumps(transform(node)))


    @istest
    def except_handler_is_converted_to_catch_for_nope_exceptions(self):
        node = cc.try_(
            [cc.ret(cc.ref("x"))],
            handlers=[cc.except_(None, None, [cc.expression_statement(cc.ref("y"))])]
        )
        
        expected = """try {
    return x;
} catch (__Nope.Internals.@__NopeException) {
    y;
}
"""
        assert_equal(expected, cs.dumps(transform(node)))
