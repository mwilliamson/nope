import re

from nose.tools import istest, assert_equal

from nope import nodes, couscous as cc, types
from nope.identity_dict import IdentityDict
from nope.desugar import desugar
from nope.name_declaration import DeclarationFinder


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
                [
                    cc.declare("value"),
                    cc.assign(cc.ref("value"), cc.none)
                ],
                is_executable=False,
                exported_names=["value"],
            ),
            type_lookup=[(module_node, module_type)]
        )


@istest
class FunctionDefinitionTests(object):
    @istest
    def test_statements_in_body_are_transformed(self):
        _assert_transform(
            nodes.func("f", nodes.args([]), [nodes.ret(nodes.ref("value"))]),
            cc.func("f", [], [cc.ret(cc.ref("value"))]),
        )
        
    @istest
    def test_variables_are_declared(self):
        _assert_transform(
            nodes.func("f", nodes.args([]), [
                nodes.assign([nodes.ref("x")], nodes.ref("y")),
                nodes.ret(nodes.ref("value")),
            ]),
            cc.func("f", [], [
                cc.declare("x"),
                cc.assign(cc.ref("x"), cc.ref("y")),
                cc.ret(cc.ref("value")),
            ]),
        )
        
    @istest
    def test_arguments_are_transformed(self):
        _assert_transform(
            nodes.func("f", nodes.args([nodes.arg("value")]), [nodes.ret(nodes.ref("value"))]),
            cc.func("f", [cc.arg("value")], [cc.ret(cc.ref("value"))]),
        )

    @istest
    def test_does_not_redeclare_variables_with_same_name_as_argument(self):
        _assert_transform(
            nodes.func(
                name="f",
                args=nodes.args([nodes.arg("x")]),
                body=[
                    nodes.assign(["x"], nodes.ref("y")),
                    nodes.ret(nodes.ref("value")),
                ],
            ),
            cc.func("f", [cc.arg("x")], [
                cc.assign(cc.ref("x"), cc.ref("y")),
                cc.ret(cc.ref("value")),
            ])
        )


    @istest
    def test_function_without_explicit_return_on_all_paths_returns_none_at_end(self):
        _assert_transform(
            nodes.func(
                name="f",
                args=nodes.args([]),
                body=[
                    nodes.if_else(
                        nodes.ref("x"),
                        [nodes.ret(nodes.boolean(True))],
                        []
                    ),
                ],
            ),
            cc.func("f", [], [
                cc.if_(
                    cc.call(cc.builtin("bool"), [cc.ref("x")]),
                    [cc.ret(cc.true)],
                ),
                cc.ret(cc.none),
            ]),
        )


@istest
class WithStatementTests(object):
    @istest
    def test_transform_with_statement_with_no_target(self):
        _assert_transform(
            nodes.with_statement(nodes.ref("manager"), None, [nodes.ret(nodes.ref("x"))]),
            """
                var $manager1 = manager
                var $exit2 = $manager1.__exit__
                var $has_exited3 = False
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
                var $manager1 = manager
                var $exit2 = $manager1.__exit__
                var $has_exited3 = False
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
class IfTests(object):
    @istest
    def test_transform_if(self):
        _assert_transform(
            nodes.if_else(
                nodes.ref("x"),
                [nodes.ret(nodes.ref("y"))],
                [nodes.ret(nodes.ref("z"))],
            ),
            cc.if_(
                cc.call(cc.builtin("bool"), [cc.ref("x")]),
                [cc.ret(cc.ref("y"))],
                [cc.ret(cc.ref("z"))],
            )
        )


@istest
class WhileLoopTests(object):
    @istest
    def test_transform_while_loop(self):
        _assert_transform(
            nodes.while_loop(
                nodes.ref("x"),
                [nodes.ret(nodes.ref("y"))],
            ),
            cc.while_(
                cc.call(cc.builtin("bool"), [cc.ref("x")]),
                [cc.ret(cc.ref("y"))],
            )
        )
        
    @istest
    def test_transform_while_loop_with_else_branch(self):
        _assert_transform(
            nodes.while_loop(
                nodes.ref("x"),
                [nodes.ret(nodes.ref("y"))],
                [nodes.ret(nodes.ref("z"))]
                
            ),
            """
                var $normal_exit0 = False
                while True:
                    if not $builtins.bool(x):
                        $normal_exit0 = True
                        break
                    return y
                if $normal_exit0:
                    return z
            """
        )


@istest
class ForLoopTests(object):
    @istest
    def test_transform_for_loop(self):
        _assert_transform(
            nodes.for_loop(
                nodes.ref("x"),
                nodes.ref("xs"),
                [nodes.ret(nodes.ref("x"))],
            ),
            """
                var $iterator0 = $builtins.iter(xs)
                var $element1
                while True:
                    $element1 = $builtins.next($iterator0, $internals.loop_sentinel)
                    if $element1 is $internals.loop_sentinel:
                        break
                    x = $element1
                    return x
            """
        )
        
    @istest
    def test_transform_for_loop_with_else_branch(self):
        _assert_transform(
            nodes.for_loop(
                nodes.ref("x"),
                nodes.ref("xs"),
                [nodes.ret(nodes.ref("x"))],
                [nodes.ret(nodes.ref("y"))],
            ),
            """
                var $iterator0 = $builtins.iter(xs)
                var $element1
                var $normal_exit2 = False
                while True:
                    $element1 = $builtins.next($iterator0, $internals.loop_sentinel)
                    if $element1 is $internals.loop_sentinel:
                        $normal_exit2 = True
                        break
                    x = $element1
                    return x
                if $normal_exit2:
                    return y
            """
        )


@istest
class BreakTests(object):
    @istest
    def test_break(self):
        _assert_transform(
            nodes.break_statement(),
            cc.break_
        )


@istest
class ContinueTests(object):
    @istest
    def test_continue(self):
        _assert_transform(
            nodes.continue_statement(),
            cc.continue_
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
    def test_transform_compound_assignments(self):
        _assert_transform(
            nodes.assign(["x", "y"], nodes.ref("z")),
            cc.statements([
                cc.declare("$tmp0", cc.ref("z")),
                cc.assign(cc.ref("x"), cc.ref("$tmp0")),
                cc.assign(cc.ref("y"), cc.ref("$tmp0")),
            ]),
        )


    @istest
    def test_tuple_assignment(self):
        _assert_transform(
            nodes.assign(
                [nodes.tuple_literal([nodes.ref("x"), nodes.ref("y")])],
                nodes.ref("z")
            ),
            """
                var $tmp0 = z
                x = $tmp0[0]
                y = $tmp0[1]
            """
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
class OperationTests(object):
    @istest
    def test_transform_binary_operation_is_converted_to_call_on_class(self):
        _assert_transform(
            nodes.add(nodes.ref("x"), nodes.ref("y")),
            cc.call(cc.attr(cc.ref("x"), "__add__"), [cc.ref("y")])
        )

    @istest
    def test_transform_unary_operation_is_converted_to_call_on_class(self):
        _assert_transform(
            nodes.neg(nodes.ref("x")),
            cc.call(cc.attr(cc.ref("x"), "__neg__"), [])
        )
        
    @istest
    def test_transform_boolean_not(self):
        _assert_transform(
            nodes.bool_not(nodes.ref("x")),
            cc.not_(cc.call(cc.builtin("bool"), [cc.ref("x")])),
        )
        
    @istest
    def test_transform_is_operator(self):
        _assert_transform(
            nodes.is_(nodes.ref("x"), nodes.ref("y")),
            cc.is_(cc.ref("x"), cc.ref("y")),
        )
        
    @istest
    def test_transform_getitem(self):
        _assert_transform(
            nodes.subscript(nodes.ref("x"), nodes.ref("y")),
            cc.call(cc.attr(cc.ref("x"), "__getitem__"), [cc.ref("y")])
        )


@istest
class CallTests(object):
    @istest
    def test_transform_call_with_positional_arguments(self):
        func_node = nodes.ref("f")
        type_lookup = [
            (func_node, types.func([types.str_type], types.none_type))
        ]
        _assert_transform(
            nodes.call(func_node, [nodes.ref("x")]),
            cc.call(cc.ref("f"), [cc.ref("x")]),
            type_lookup=type_lookup,
        )
        
    @istest
    def test_transform_call_with_keyword_arguments(self):
        func_node = nodes.ref("f")
        type_lookup = [
            (func_node, types.func(
                [
                    types.func_arg("first", types.str_type),
                    types.func_arg("second", types.str_type),
                ],
                types.none_type
            ))
        ]
        
        _assert_transform(
            nodes.call(func_node, [], {"first": nodes.ref("x"), "second": nodes.ref("y")}),
            cc.call(cc.ref("f"), [cc.ref("x"), cc.ref("y")]),
            type_lookup=type_lookup,
        )


    @istest
    def test_transform_call_with_optional_positional_argument(self):
        func_node = nodes.ref("f")
        type_lookup = [
            (func_node, types.func(
                [types.str_type, types.func_arg(None, types.str_type, optional=True)],
                types.none_type
            ))
        ]
        
        _assert_transform(
            nodes.call(func_node, [nodes.ref("x")]),
            cc.call(cc.ref("f"), [cc.ref("x"), cc.none]),
            type_lookup=type_lookup,
        )


    @istest
    def test_transform_call_magic_method(self):
        func_node = nodes.ref("str")
        type_lookup = [
            (func_node, types.str_meta_type)
        ]
        
        _assert_transform(
            nodes.call(func_node, [nodes.ref("x")]),
            """str.__call__(x)""",
            type_lookup=type_lookup,
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
class StringLiteralTests(object):
    @istest
    def test_transform(self):
        _assert_transform(
            nodes.string("Many places I have been"),
            cc.str_literal("Many places I have been")
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
class BooleanLiteralTests(object):
    @istest
    def test_transform(self):
        _assert_transform(nodes.boolean(True), cc.true)
        _assert_transform(nodes.boolean(False), cc.false)


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
    result = desugar(nope, type_lookup=type_lookup, declarations=DeclarationFinder())
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
