import collections

from nose.tools import istest, assert_equal

from nope.platforms.dotnet import cs

@istest
class TryStatements(object):
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
