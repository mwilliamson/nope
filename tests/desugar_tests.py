import re

from nose.tools import istest, assert_equal

from nope import nodes, couscous as cc, types
from nope.identity_dict import IdentityDict
from nope.desugar import desugar
from nope.name_declaration import DeclarationFinder
from nope.module_resolution import ResolvedImport


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
class ImportTests(object):
    @istest
    def test_import_of_module_assigns_module_to_name(self):
        _assert_transform(
            nodes.import_([nodes.import_alias("message", None)]),
            cc.assign(cc.ref("message"), cc.module_ref(["message"]))
        )
        
    @istest
    def test_import_of_module_assigns_module_to_as_name_if_present(self):
        _assert_transform(
            nodes.import_([nodes.import_alias("message", "m")]),
            cc.assign(cc.ref("m"), cc.module_ref(["message"]))
        )
        
    @istest
    def test_import_multiple_values_in_single_import_statement(self):
        _assert_transform(
            nodes.import_([
                nodes.import_alias("os", None),
                nodes.import_alias("sys", None)
            ]),
            cc.statements([
                cc.assign(cc.ref("os"), cc.module_ref(["os"])),
                cc.assign(cc.ref("sys"), cc.module_ref(["sys"])),
            ])
        )
        
    @istest
    def test_import_of_module_in_package_assigns_values_for_both_package_and_module(self):
        _assert_transform(
            nodes.import_([
                nodes.import_alias("os.path", None),
            ]),
            cc.statements([
                cc.assign(cc.ref("os"), cc.module_ref(["os"])),
                cc.assign(cc.attr(cc.ref("os"), "path"), cc.module_ref(["os", "path"])),
            ])
        )


@istest
class ImportFromTests(object):
    @istest
    def test_import_from_assigns_value_to_name_of_value_if_asname_is_not_set(self):
        _assert_transform(
            nodes.import_from(["os", "path"], [nodes.import_alias("join", None)]),
            cc.assign(cc.ref("join"), cc.attr(cc.module_ref(["os", "path"]), "join")),
        )
        
    @istest
    def test_import_from_assigns_value_to_asname_if_asname_is_set(self):
        _assert_transform(
            nodes.import_from(["os", "path"], [nodes.import_alias("join", "j")]),
            cc.assign(cc.ref("j"), cc.attr(cc.module_ref(["os", "path"]), "join")),
        )
        
    @istest
    def test_import_from_uses_two_dots_to_indicate_import_from_parent_package(self):
        _assert_transform(
            nodes.import_from([".."], [nodes.import_alias("x", None)]),
            cc.assign(cc.ref("x"), cc.attr(cc.module_ref([".."]), "x")),
        )
    
    @istest
    def test_multiple_imported_names_in_one_statement_generates_multiple_assignments(self):
        _assert_transform(
            nodes.import_from(["."], [
                nodes.import_alias("x", None),
                nodes.import_alias("y", None),
            ]),
            cc.statements([
                cc.assign(cc.ref("x"), cc.attr(cc.module_ref(["."]), "x")),
                cc.assign(cc.ref("y"), cc.attr(cc.module_ref(["."]), "y")),
            ]),
        )
        
    @istest
    def test_importing_module_from_package_references_module_directly(self):
        module_resolver = FakeModuleResolver({
            (("x", ), "y"): ResolvedImport(["x", "y"], _stub_module, None)
        })
        _assert_transform(
            nodes.import_from(["x"], [nodes.import_alias("y", None)]),
            cc.assign(cc.ref("y"), cc.module_ref(["x", "y"])),
            module_resolver=module_resolver,
        )
    

_stub_module = object()

class FakeModuleResolver(object):
    def __init__(self, imports=None):
        if imports is None:
            imports = {}
        
        self._imports = imports
    
    def resolve_import_value(self, names, value_name):
        return self._imports.get(
            (tuple(names), value_name),
            ResolvedImport(names, _stub_module, value_name)
        )


@istest
class ClassDefinitionTests(object):
    @istest
    def test_assignments_in_body_are_transformed(self):
        _assert_transform(
            nodes.class_("Blah", [nodes.assign([nodes.ref("value")], nodes.none())]),
            cc.class_(
                "Blah",
                methods=[],
                body=[
                    cc.declare("value"),
                    cc.assign(cc.ref("value"), cc.none),
                ],
            ),
        )
    
    @istest
    def test_function_definitions_in_body_are_stored_as_methods(self):
        _assert_transform(
            nodes.class_("Blah", [nodes.func("f", nodes.args([]), [])]),
            cc.class_(
                "Blah",
                methods=[cc.func("f", [], [cc.ret(cc.none)])],
                body=[cc.declare("f")],
            ),
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
    def test_does_not_redeclare_variables_with_same_name_as_type_parameter(self):
        _assert_transform(
            nodes.typed(
                nodes.signature(
                    type_params=[nodes.formal_type_parameter("T")],
                    args=[],
                    returns=nodes.ref("T"),
                ),
                nodes.func(
                    name="f",
                    args=nodes.args([]),
                    body=[],
                ),
            ),
            cc.func("f", [], [
                cc.ret(cc.none),
            ])
        )


    @istest
    def test_function_without_explicit_return_on_all_paths_returns_none_at_end(self):
        _assert_transform(
            nodes.func(
                name="f",
                args=nodes.args([]),
                body=[
                    nodes.if_(
                        nodes.ref("x"),
                        [nodes.ret(nodes.bool_literal(True))],
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
class TryStatementTests(object):
    @istest
    def test_statements_in_bodies_are_transformed(self):
        _assert_transform(
            nodes.try_(
                [nodes.ret(nodes.ref("x"))],
                handlers=[nodes.except_(nodes.ref("Exception"), nodes.ref("error"), [nodes.ref("y")])],
                finally_body=[nodes.ret(nodes.ref("z"))],
            ),
            cc.try_(
                [cc.ret(cc.ref("x"))],
                handlers=[cc.except_(cc.ref("Exception"), cc.ref("error"), [cc.ref("y")])],
                finally_body=[cc.ret(cc.ref("z"))],
            ),
        )


@istest
class WithStatementTests(object):
    @istest
    def test_transform_with_statement_with_no_target(self):
        _assert_transform(
            nodes.with_(nodes.ref("manager"), None, [nodes.ret(nodes.ref("x"))]),
            """
                var __nope_u_exception0
                var __nope_u_manager1 = manager
                var __nope_u_exit2 = __nope_u_manager1.__exit__
                var __nope_u_has_exited3 = False
                __nope_u_manager1.__enter__()
                try:
                    return x
                except $builtins.Exception as __nope_u_exception0:
                    __nope_u_has_exited3 = True
                    if not $builtins.bool(__nope_u_exit2($builtins.type(__nope_u_exception0), __nope_u_exception0, None)):
                        raise
                finally:
                    if not __nope_u_has_exited3:
                        __nope_u_exit2(None, None, None)
            """
        )


    @istest
    def test_transform_with_statement_with_target(self):
        _assert_transform(
            nodes.with_(nodes.ref("manager"), nodes.ref("value"), [nodes.ret(nodes.ref("x"))]),
            """
                var __nope_u_exception0
                var __nope_u_manager1 = manager
                var __nope_u_exit2 = __nope_u_manager1.__exit__
                var __nope_u_has_exited3 = False
                value = __nope_u_manager1.__enter__()
                try:
                    return x
                except $builtins.Exception as __nope_u_exception0:
                    __nope_u_has_exited3 = True
                    if not $builtins.bool(__nope_u_exit2($builtins.type(__nope_u_exception0), __nope_u_exception0, None)):
                        raise
                finally:
                    if not __nope_u_has_exited3:
                        __nope_u_exit2(None, None, None)
            """
        )


@istest
class IfTests(object):
    @istest
    def test_condition_is_transformed_using_bool_builtin(self):
        _assert_transform(
            nodes.if_(
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
    def test_condition_is_not_transformed_using_bool_builtin_if_already_a_bool(self):
        condition_node = nodes.ref("x")
        _assert_transform(
            nodes.if_(
                condition_node,
                [nodes.ret(nodes.ref("y"))],
                [nodes.ret(nodes.ref("z"))],
            ),
            cc.if_(
                cc.ref("x"),
                [cc.ret(cc.ref("y"))],
                [cc.ret(cc.ref("z"))],
            ),
            type_lookup=[
                (condition_node, types.bool_type),
            ],
        )


@istest
class WhileLoopTests(object):
    @istest
    def test_transform_while_loop(self):
        _assert_transform(
            nodes.while_(
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
            nodes.while_(
                nodes.ref("x"),
                [nodes.ret(nodes.ref("y"))],
                [nodes.ret(nodes.ref("z"))]
                
            ),
            """
                var __nope_u_normal_exit0 = False
                while True:
                    if not $builtins.bool(x):
                        __nope_u_normal_exit0 = True
                        break
                    return y
                if __nope_u_normal_exit0:
                    return z
            """
        )


@istest
class ForLoopTests(object):
    @istest
    def test_transform_for_loop(self):
        _assert_transform(
            nodes.for_(
                nodes.ref("x"),
                nodes.ref("xs"),
                [nodes.ret(nodes.ref("x"))],
            ),
            """
                var __nope_u_iterator0 = $builtins.iter(xs)
                var __nope_u_element1
                while True:
                    __nope_u_element1 = $builtins.next(__nope_u_iterator0, $internals.loop_sentinel)
                    if __nope_u_element1 is $internals.loop_sentinel:
                        break
                    x = __nope_u_element1
                    return x
            """
        )
        
    @istest
    def test_transform_for_loop_with_else_branch(self):
        _assert_transform(
            nodes.for_(
                nodes.ref("x"),
                nodes.ref("xs"),
                [nodes.ret(nodes.ref("x"))],
                [nodes.ret(nodes.ref("y"))],
            ),
            """
                var __nope_u_iterator0 = $builtins.iter(xs)
                var __nope_u_element1
                var __nope_u_normal_exit2 = False
                while True:
                    __nope_u_element1 = $builtins.next(__nope_u_iterator0, $internals.loop_sentinel)
                    if __nope_u_element1 is $internals.loop_sentinel:
                        __nope_u_normal_exit2 = True
                        break
                    x = __nope_u_element1
                    return x
                if __nope_u_normal_exit2:
                    return y
            """
        )


@istest
class BreakTests(object):
    @istest
    def test_break(self):
        _assert_transform(
            nodes.break_(),
            cc.break_
        )


@istest
class ContinueTests(object):
    @istest
    def test_continue(self):
        _assert_transform(
            nodes.continue_(),
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
class RaiseStatementTests(object):
    @istest
    def test_transform_raise_statement_transforms_value(self):
        _assert_transform(
            nodes.raise_(nodes.ref("value")),
            cc.raise_(cc.ref("value"))
        )


@istest
class AssertStatementTests(object):
    @istest
    def test_assert_without_message_is_transformed_to_conditional_raise(self):
        _assert_transform(
            nodes.assert_(nodes.ref("value")),
            """
                if not value:
                    raise $builtins.AssertionError.__call__("")
            """
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
                cc.declare("__nope_u_tmp0", cc.ref("z")),
                cc.assign(cc.ref("x"), cc.ref("__nope_u_tmp0")),
                cc.assign(cc.ref("y"), cc.ref("__nope_u_tmp0")),
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
                var __nope_u_tmp0 = z
                x = __nope_u_tmp0.__getitem__(0)
                y = __nope_u_tmp0.__getitem__(1)
            """
        )


    @istest
    def test_transform_setitem_subscript(self):
        _assert_transform(
            nodes.assign([nodes.subscript(nodes.ref("x"), nodes.ref("y"))], nodes.ref("z")),
            """
                var __nope_u_tmp0 = z
                x.__setitem__(y, __nope_u_tmp0)
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
    def test_transform_boolean_and(self):
        _assert_transform(
            nodes.bool_and(nodes.ref("x"), nodes.ref("y")),
            cc.ternary_conditional(
                cc.call(cc.builtin("bool"), [cc.ref("x")]),
                cc.ref("y"),
                cc.ref("x")
            ),
        )
        
    @istest
    def test_transform_boolean_or(self):
        _assert_transform(
            nodes.bool_or(nodes.ref("x"), nodes.ref("y")),
            cc.ternary_conditional(
                cc.call(cc.builtin("bool"), [cc.ref("x")]),
                cc.ref("x"),
                cc.ref("y")
            ),
        )
        
    @istest
    def test_transform_is_operator(self):
        _assert_transform(
            nodes.is_(nodes.ref("x"), nodes.ref("y")),
            cc.is_(cc.ref("x"), cc.ref("y")),
        )
        
    @istest
    def test_transform_is_not_operator(self):
        _assert_transform(
            nodes.is_not(nodes.ref("x"), nodes.ref("y")),
            cc.is_not(cc.ref("x"), cc.ref("y")),
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
class ListLiteralTests(object):
    @istest
    def test_transform(self):
        _assert_transform(
            nodes.list_literal([nodes.none()]),
            cc.list_literal([cc.none])
        )


@istest
class TupleLiteralTests(object):
    @istest
    def test_transform(self):
        _assert_transform(
            nodes.tuple_literal([nodes.none()]),
            cc.tuple_literal([cc.none])
        )


@istest
class SliceTests(object):
    @istest
    def test_transform(self):
        _assert_transform(
            nodes.slice(nodes.ref("x"), nodes.ref("y"), nodes.none()),
            cc.call(cc.builtin("slice"), [cc.ref("x"), cc.ref("y"), cc.none]),
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
            nodes.str_literal("Many places I have been"),
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
        _assert_transform(nodes.bool_literal(True), cc.true)
        _assert_transform(nodes.bool_literal(False), cc.false)


@istest
class NoneLiteralTests(object):
    @istest
    def test_transform(self):
        _assert_transform(
            nodes.none(),
            cc.none
        )


def _assert_transform(nope, expected_result, type_lookup=None, module_resolver=None):
    if type_lookup is None:
        type_lookup = []
    
    if module_resolver is None:
        module_resolver = FakeModuleResolver()
    
    type_lookup = types.TypeLookup(IdentityDict(type_lookup))
    
    result = desugar(nope, type_lookup=type_lookup, declarations=DeclarationFinder(), module_resolver=module_resolver)
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
