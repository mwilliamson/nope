import re

from nose.tools import istest, assert_equal

from nope import nodes, couscous as cc, types
from nope.identity_dict import IdentityDict
from nope.desugar import desugar


@istest
class ModuleTests(object):
    @istest
    def test_statements_in_module_body_are_transformed(self):
        module_node = nodes.module([nodes.expression_statement(nodes.ref("value"))], is_executable=True)
        module_type = types.module("blah", [])
        _assert_transform(
            module_node,
            cc.module([cc.expression_statement(cc.ref("value"))], is_executable=True, exported_names=[]),
            type_lookup=[(module_node, module_type)]
        )
        
    @istest
    def test_module_exports_are_set_directly_on_module(self):
        module_node = nodes.module(
            [nodes.assign([nodes.ref("value")], nodes.none())],
            is_executable=False
        )
        module_type = types.module("blah", [types.attr("value", types.none_type)])
        _assert_transform(
            module_node,
            cc.module(
                [cc.assign(cc.ref("value"), cc.none)],
                is_executable=False,
                exported_names=["value"],
            ),
            type_lookup=[(module_node, module_type)]
        )


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
class FunctionDefinitionTests(object):
    @istest
    def test_transform_body(self):
        _assert_transform(
            nodes.func("f", nodes.args([]), [nodes.ret(nodes.ref("value"))]),
            cc.func("f", [], [cc.ret(cc.ref("value"))]),
        )
        
    @istest
    def test_transform_args(self):
        _assert_transform(
            nodes.func("f", nodes.args([nodes.arg("value")]), []),
            cc.func("f", [cc.arg("value")], []),
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
class AssignmentTests(object):
    @istest
    def test_transform_assigment_to_single_target(self):
        _assert_transform(
            nodes.assign([nodes.ref("x")], nodes.ref("y")),
            cc.assign(cc.ref("x"), cc.ref("y")),
        )
        

@istest
class ExpressionStatementTests(object):
    @istest
    def test_transform_value(self):
        _assert_transform(
            nodes.expression_statement(nodes.ref("value")),
            cc.expression_statement(cc.ref("value"))
        )


@istest
class CallTests(object):
    @istest
    def callee_is_transformed(self):
        _assert_transform(
            nodes.call(nodes.ref("f"), []),
            cc.call(cc.ref("f"), []),
        )
        
    @istest
    def arguments_are_transformed(self):
        _assert_transform(
            nodes.call(nodes.ref("f"), [nodes.ref("x")]),
            cc.call(cc.ref("f"), [cc.ref("x")]),
        )


@istest
class VariableReferenceTests(object):
    @istest
    def variable_reference_is_tranformed_to_reference_of_same_name(self):
        _assert_transform(
            nodes.ref("value"),
            cc.ref("value")
        )


@istest
class IntLiteralTests(object):
    @istest
    def test_transform(self):
        _assert_transform(
            nodes.int_literal(42),
            cc.int_literal(42)
        )


@istest
class NoneLiteralTests(object):
    @istest
    def test_transform(self):
        _assert_transform(
            nodes.none(),
            cc.none
        )


def _assert_transform(nope, expected_result, type_lookup=None):
    if type_lookup is not None:
        type_lookup = types.TypeLookup(IdentityDict(type_lookup))
    result = desugar(nope, type_lookup=type_lookup)
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
