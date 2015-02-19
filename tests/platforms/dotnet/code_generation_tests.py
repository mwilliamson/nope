import os

from nose.tools import istest, assert_equal

from nope import couscous as cc
from nope.platforms.dotnet import cs
from nope.platforms.dotnet.codegeneration import _transform as transform


@istest
class FunctionDefinitionTests(object):
    @istest
    def function_with_zero_arguments_is_converted_to_csharp_lambda_assignment(self):
        node = cc.func("f", [], [cc.ret(cc.int_literal(42))])
        
        expected = """
f = ((System.Func<dynamic>)(() =>
{
    return 42;
}
));"""
        assert_equal(expected.strip(), cs.dumps(transform(node)).strip())
        
    @istest
    def function_with_multiple_arguments_is_converted_to_csharp_lambda_assignment_with_dynamic_args(self):
        node = cc.func("f", [cc.arg("x"), cc.arg("y")], [cc.ret(cc.int_literal(42))])
        
        expected = """
f = ((System.Func<dynamic, dynamic, dynamic>)((dynamic x, dynamic y) =>
{
    return 42;
}
));"""
        assert_equal(expected.strip(), cs.dumps(transform(node)).strip())
