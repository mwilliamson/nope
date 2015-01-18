import re

from nose.tools import istest, assert_equal

from nope import nodes, couscous as cc
from nope.desugar import desugar


@istest
class WithStatementTests(object):
    @istest
    def test_transform_with_statement_with_no_target(self):
        _assert_transform(
            nodes.with_statement(nodes.ref("manager"), None, [nodes.ret(nodes.ref("x"))]),
            """
                $manager1 = manager
                $exit2 = $manager1.__exit__
                $has_exited3 = False
                $manager1.__enter__()
                try:
                    return x
                except $builtins.Exception as $exception0:
                    $has_exited3 = True
                    if not $builtins.bool($exit2($builtins.type($exception0), $exception0, None)):
                        raise
                finally:
                    if not $has_exited3:
                        $exit2(None, None, None)
            """
        )


    @istest
    def test_transform_with_statement_with_target(self):
        _assert_transform(
            nodes.with_statement(nodes.ref("manager"), nodes.ref("value"), [nodes.ret(nodes.ref("x"))]),
            """
                $manager1 = manager
                $exit2 = $manager1.__exit__
                $has_exited3 = False
                value = $manager1.__enter__()
                try:
                    return x
                except $builtins.Exception as $exception0:
                    $has_exited3 = True
                    if not $builtins.bool($exit2($builtins.type($exception0), $exception0, None)):
                        raise
                finally:
                    if not $has_exited3:
                        $exit2(None, None, None)
            """
        )


@istest
class ReturnStatementTests(object):
    @istest
    def test_transform_return_statement_transforms_value(self):
        _assert_transform(
            nodes.ret(nodes.ref("value")),
            cc.ret(cc.ref("value"))
        )


@istest
class VariableReferenceTests(object):
    @istest
    def variable_reference_is_tranformed_to_reference_of_same_name(self):
        _assert_transform(
            nodes.ref("value"),
            cc.ref("value")
        )


def _assert_transform(nope, expected_result):
    result = desugar(nope)
    if isinstance(expected_result, str):
        lines = list(filter(lambda line: line.strip(), expected_result.splitlines()))
        indentation = re.match("^ *", lines[0]).end()
        reindented_lines = [
            line[indentation:]
            for line in lines
        ]
        
        assert_equal("\n".join(reindented_lines), cc.dumps(result).strip())
    else:
        assert_equal(expected_result, result)
