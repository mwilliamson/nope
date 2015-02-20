import slimit.parser
from nose.tools import istest, assert_equal

from nope.platforms.nodejs import js
from nope.platforms.nodejs.transform import NodeTransformer
from nope import couscous as cc
from nope.module_resolution import ResolvedImport
from nope.modules import BuiltinModule


@istest
def test_transform_module():
    _assert_transform(
        cc.module([cc.expression_statement(cc.ref("x"))], is_executable=False, exported_names=[]),
        js.statements([js.expression_statement(js.ref("x"))])
    )


@istest
def test_transform_module_with_exports():
    _assert_transform(
        cc.module([
            cc.declare("__all__"),
            cc.declare("x"),
            cc.assign(cc.ref("__all__"), cc.list_literal([cc.str_literal("x")])),
            cc.assign(cc.ref("x"), cc.none)
        ], exported_names=["x"]),
        """
            var __all__;
            var x;
            __all__ = ["x"];
            x = null;
            $exports.x = x;
        """
    )


@istest
def test_transform_basic_import_of_top_level_module():
    _assert_transform(
        cc.import_([cc.import_alias("x", None)]),
        js.statements([
            js.assign_statement("x", js.call(js.ref("$require"), [js.string("x")])),
        ])
    )


@istest
def test_transform_basic_import_of_module_in_package():
    _assert_transform(
        cc.import_([cc.import_alias("x.y", None)]),
        js.statements([
            js.assign_statement("x", js.call(js.ref("$require"), [js.string("x")])),
            js.assign_statement(js.property_access(js.ref("x"), "y"), js.call(js.ref("$require"), [js.string("x/y")])),
        ])
    )


@istest
def test_transform_import_from_current_package():
    _assert_transform(
        cc.import_from(["."], [cc.import_alias("x", None)]),
        """
            x = ($require("./")).x;
        """
    )


@istest
def test_transform_import_from_parent_package():
    _assert_transform(
        cc.import_from([".."], [cc.import_alias("x", None)]),
        """
            x = ($require("../")).x
        """
    )


@istest
def test_transform_import_from_with_multiple_names():
    _assert_transform(
        cc.import_from(["."], [
            cc.import_alias("x", None),
            cc.import_alias("y", None),
        ]),
        """
            x = ($require("./")).x;
            y = ($require("./")).y;
        """
    )


@istest
def test_transform_import_from_with_alias():
    _assert_transform(
        cc.import_from(["."], [
            cc.import_alias("x", "y"),
        ]),
        """
            y = ($require("./")).x
        """
    )


@istest
def test_transform_import_from_child_package():
    _assert_transform(
        cc.import_from([".", "x"], [cc.import_alias("y", None)]),
        """
            y = ($require("./x")).y
        """
    )


@istest
def test_transform_import_module_from_absolute_package():
    _assert_transform(
        cc.import_from(["x"], [cc.import_alias("y", None)]),
        """
            y = ($require("x")).y;
        """
    )


@istest
def test_transform_import_value_from_absolute_package():
    _assert_transform(
        cc.import_from(["x"], [cc.import_alias("y", None)]),
        """
            y = $require("x/y");
        """,
        module_resolver=FakeModuleResolver({
            (("x", ), "y"): ResolvedImport(["x", "y"], _stub_module, None)
        })
    )


@istest
def test_transform_import_builtin_module():
    module = BuiltinModule("cgi", None)
    _assert_transform(
        cc.import_([cc.import_alias("cgi", None)]),
        """
            cgi = $require("__builtins/cgi");
        """,
        module_resolver=FakeModuleResolver({
            (("cgi", ), None): ResolvedImport(["cgi"], module, None)
        })
    )


@istest
def test_transform_expression_statement():
    _assert_transform(
        cc.expression_statement(cc.ref("x")),
        js.expression_statement(js.ref("x"))
    )


@istest
def test_transform_function_declaration():
    _assert_transform(
        cc.func(
            name="f",
            args=[cc.arg("x"), cc.arg("y")],
            body=[cc.ret(cc.ref("x"))],
        ),
        js.function_declaration(
            name="f",
            args=["x", "y"],
            body=[js.ret(js.ref("x"))],
        )
    )


@istest
def test_transform_empty_class():
    _assert_transform(
        cc.class_(
            name="User",
            methods=[],
            body=[],
        ),
        """
            User = function() {
                var $self0 = {};
                return $self0;
            };
        """
    )


@istest
def test_transform_class_with_attributes():
    _assert_transform(
        cc.class_(
            name="User",
            methods=[],
            body=[
                cc.declare("x"),
                cc.assign(cc.ref("x"), cc.none)
            ],
        ),
        """
            User = function() {
                var $self0 = {};
                var x;
                x = null;
                $self0.x = $nope.instanceAttribute($self0, x);
                return $self0;
            };
        """
    )


@istest
def test_transform_class_with_methods():
    _assert_transform(
        cc.class_(
            name="User",
            methods=[
                cc.func(
                    "f",
                    [cc.arg("self"), cc.arg("x")],
                    [cc.ret(cc.none)],
                )
            ],
            body=[]
        ),
        """
            function $f0(self, x) {
                return null;
            }
            User = function() {
                var $self1 = {};
                $self1.f = $nope.instanceAttribute($self1, $f0);
                return $self1;
            };
        """
    )


@istest
def test_transform_class_with_init_method():
    class_node = cc.class_(
        name="User",
        methods=[
            cc.func(
                "__init__",
                [cc.arg("self"), cc.arg("x")],
                [],
            )
        ],
        body=[],
    )
    _assert_transform(
        class_node,
        """
            function $__init__0(self, x) {
            }
            User = function($arg1) {
                var $self2 = {};
                $__init__0($self2, $arg1);
                return $self2;
            };
        """,
    )


@istest
def test_transform_assignment():
    _assert_transform(
        cc.assign(cc.ref("x"), cc.ref("z")),
        js.expression_statement(js.assign(js.ref("x"), js.ref("z"))),
    )


@istest
def test_transform_assignment_to_attribute_sets_property_directly():
    _assert_transform(
        cc.assign(cc.attr(cc.ref("x"), "y"), cc.ref("z")),
        js.expression_statement(js.assign(js.property_access(js.ref("x"), "y"), js.ref("z"))),
    )


@istest
def test_transform_return():
    _assert_transform(
        cc.ret(cc.ref("x")),
        js.ret(js.ref("x"))
    )


@istest
def test_transform_if_else():
    _assert_transform(
        cc.if_(
            cc.ref("x"),
            [cc.ret(cc.ref("y"))],
            [cc.ret(cc.ref("z"))],
        ),
        js.if_else(
            js.ref("x"),
            [js.ret(js.ref("y"))],
            [js.ret(js.ref("z"))],
        )
    )


@istest
def test_transform_while_loop():
    _assert_transform(
        cc.while_(
            cc.ref("x"),
            [cc.ret(cc.ref("y"))],
        ),
        js.while_loop(
            js.ref("x"),
            [js.ret(js.ref("y"))],
        )
    )


@istest
def test_transform_break():
    _assert_transform(
        cc.break_,
        js.break_statement(),
    )


@istest
def test_transform_continue():
    _assert_transform(
        cc.continue_,
        js.continue_statement(),
    )


@istest
def test_transform_try_with_empty_finally_body():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            finally_body=[],
        ),
        """
            return x;
        """,
    )


@istest
def test_transform_try_finally():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            finally_body=[cc.ret(cc.ref("y"))],
        ),
        """
            try {
                return x;
            } finally {
                return y;
            }
        """,
    )


@istest
def test_transform_try_except_with_no_name():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            handlers=[
                cc.except_(None, None, [cc.ret(cc.ref("y"))]),
            ],
        ),
        """
            try {
                return x;
            } catch ($exception0) {
                if (($exception0.$nopeException) === ($nope.undefined)) {
                    throw $exception0;
                } else {
                    if ($nope.builtins.isinstance($exception0.$nopeException, $nope.builtins.Exception)) {
                        return y;
                    } else {
                        throw $exception0;
                    }
                }
            }
        """,
    )


@istest
def test_transform_try_except_with_exception_type():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            handlers=[
                cc.except_(cc.ref("AssertionError"), None, [cc.ret(cc.ref("y"))]),
            ],
        ),
        """
            try {
                return x;
            } catch ($exception0) {
                if (($exception0.$nopeException) === ($nope.undefined)) {
                    throw $exception0;
                } else {
                    if ($nope.builtins.isinstance($exception0.$nopeException, AssertionError)) {
                        return y;
                    } else {
                        throw $exception0;
                    }
                }
            }
        """,
    )


@istest
def test_transform_try_except_with_exception_type_and_name():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            handlers=[
                cc.except_(cc.ref("AssertionError"), cc.ref("error"), [cc.ret(cc.ref("y"))]),
            ],
        ),
        """
            try {
                return x;
            } catch ($exception0) {
                if (($exception0.$nopeException) === ($nope.undefined)) {
                    throw $exception0;
                } else {
                    if ($nope.builtins.isinstance($exception0.$nopeException, AssertionError)) {
                        var error = $exception0.$nopeException;
                        return y;
                    } else {
                        throw $exception0;
                    }
                }
            }
        """,
    )


@istest
def test_transform_try_with_empty_except_body():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            handlers=[
                cc.except_(cc.ref("AssertionError"), cc.ref("error"), []),
            ],
        ),
        """
            try {
                return x;
            } catch ($exception0) {
                if (($exception0.$nopeException) === ($nope.undefined)) {
                    throw $exception0;
                } else {
                    if ($nope.builtins.isinstance($exception0.$nopeException, AssertionError)) {
                        var error = $exception0.$nopeException;
                    } else {
                        throw $exception0;
                    }
                }
            }
        """,
    )


@istest
def test_transform_try_except_with_multiple_exception_handlers():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            handlers=[
                cc.except_(cc.ref("AssertionError"), None, [cc.ret(cc.ref("y"))]),
                cc.except_(cc.ref("Exception"), None, [cc.ret(cc.ref("z"))]),
            ],
        ),
        """
            try {
                return x;
            } catch ($exception0) {
                if (($exception0.$nopeException) === ($nope.undefined)) {
                    throw $exception0;
                } else {
                    if ($nope.builtins.isinstance($exception0.$nopeException, AssertionError)) {
                        return y;
                    } else {
                        if ($nope.builtins.isinstance($exception0.$nopeException, Exception)) {
                            return z;
                        } else {
                            throw $exception0;
                        }
                    }
                }
            }
        """,
    )


@istest
def test_transform_raise_without_exception_value():
    _assert_transform(
        cc.try_(
            [cc.ret(cc.ref("x"))],
            handlers=[
                cc.except_(cc.ref("AssertionError"), cc.ref("error"), [cc.raise_()]),
            ],
        ),
        """
            try {
                return x;
            } catch ($exception0) {
                if (($exception0.$nopeException) === ($nope.undefined)) {
                    throw $exception0;
                } else {
                    if ($nope.builtins.isinstance($exception0.$nopeException, AssertionError)) {
                        var error = $exception0.$nopeException;
                        throw $exception0;
                    } else {
                        throw $exception0;
                    }
                }
            }
        """,
    )


@istest
def test_transform_raise_with_exception_value():
    _assert_transform(
        cc.raise_(cc.ref("error")),
        """
            var $exception0 = error;
            var $error1 = new $nope.Error();
            $error1.$nopeException = $exception0;
            $error1.toString = function() {
                return (($nope.builtins.getattr($nope.builtins.type($exception0), "__name__")) + ": ") + ($nope.builtins.str($exception0));
            };
            throw $error1;
        """,
    )


@istest
def test_transform_call_with_positional_arguments():
    _assert_transform(
        cc.call(cc.ref("f"), [cc.ref("x"), cc.ref("y")]),
        js.call(js.ref("f"), [js.ref("x"), js.ref("y")]),
    )


@istest
def test_transform_attribute_access():
    _assert_transform(
        cc.attr(cc.ref("x"), "y"),
        js.call(js.ref("$nope.builtins.getattr"), [js.ref("x"), js.string("y")])
    )

# TODO:
#~ @istest
#~ def test_normal_js_addition_is_used_if_both_operands_are_ints_and_optimise_is_true():
    #~ left = nodes.ref("x")
    #~ right = nodes.ref("y")
    #~ 
    #~ type_lookup = types.TypeLookup(IdentityDict([
        #~ (left, types.int_type),
        #~ (right, types.int_type),
    #~ ]))
    #~ 
    #~ def assert_transform(expected_js, optimise):
        #~ _assert_transform(
            #~ nodes.add(left, right),
            #~ expected_js,
            #~ type_lookup=type_lookup,
            #~ optimise=optimise,
        #~ )
    #~ 
    #~ assert_transform(js.binary_operation("+", js.ref("x"), js.ref("y")), optimise=True)
    #~ assert_transform(js.call(js.ref("$nope.operators.add"), [js.ref("x"), js.ref("y")]), optimise=False)
    #~ 
    #~ # Doing this in the same test to make sure all arguments except optimise are the same
    

#~ @istest
#~ def test_normal_binary_operation_if_only_one_side_is_int():
    #~ x = nodes.ref("x")
    #~ y = nodes.ref("y")
    #~ 
    #~ type_lookup = types.TypeLookup(IdentityDict([
        #~ (x, types.int_type),
        #~ (y, types.object_type),
    #~ ]))
    #~ 
    #~ _assert_transform(
        #~ nodes.add(x, y),
        #~ js.call(js.ref("$nope.operators.add"), [js.ref("x"), js.ref("y")]),
        #~ type_lookup=type_lookup,
    #~ )
    #~ 
    #~ _assert_transform(
        #~ nodes.add(y, x),
        #~ js.call(js.ref("$nope.operators.add"), [js.ref("y"), js.ref("x")]),
        #~ type_lookup=type_lookup,
    #~ )


#~ @istest
#~ def test_normal_javascript_negation_is_used_if_operand_is_int():
    #~ x = nodes.ref("x")
    #~ 
    #~ type_lookup = types.TypeLookup(IdentityDict([
        #~ (x, types.int_type),
    #~ ]))
    #~ 
    #~ _assert_transform(
        #~ nodes.neg(x),
        #~ js.unary_operation("-", js.ref("x")),
        #~ type_lookup=type_lookup,
    #~ )


@istest
def test_transform_ternary_conditional():
    _assert_transform(
        cc.ternary_conditional(cc.ref("x"), cc.ref("y"), cc.ref("z")),
        js.ternary_conditional(js.ref("x"), js.ref("y"), js.ref("z")),
    )


@istest
def test_transform_boolean_not():
    _assert_transform(
        cc.not_(cc.ref("x")),
        js.unary_operation("!", js.ref("x")),
    )


@istest
def test_transform_boolean_and():
    _assert_transform(
        cc.and_(cc.ref("x"), cc.ref("y")),
        js.and_(js.ref("x"), js.ref("y")),
    )


@istest
def test_transform_boolean_or():
    _assert_transform(
        cc.or_(cc.ref("x"), cc.ref("y")),
        js.or_(js.ref("x"), js.ref("y")),
    )


@istest
def test_transform_is_operation():
    _assert_transform(
        cc.is_(cc.ref("x"), cc.ref("y")),
        js.binary_operation("===", js.ref("x"), js.ref("y"))
    )


@istest
def test_transform_variable_reference():
    _assert_transform(
        cc.ref("x"),
        js.ref("x")
    )


@istest
def test_transform_builtin_reference():
    _assert_transform(
        cc.builtin("x"),
        js.ref("$nope.builtins.x")
    )


@istest
def test_transform_none_expression():
    _assert_transform(
        cc.none,
        js.null
    )


@istest
def test_transform_boolean_expression():
    _assert_transform(
        cc.true,
        js.boolean(True)
    )
    _assert_transform(
        cc.false,
        js.boolean(False)
    )


@istest
def test_transform_string_expression():
    _assert_transform(
        cc.str_literal("hello"),
        js.string("hello")
    )


@istest
def test_transform_int_expression():
    _assert_transform(
        cc.int_literal(42),
        js.number(42),
    )


@istest
def test_transform_tuple_literal():
    _assert_transform(
        cc.tuple_literal([cc.int_literal(42), cc.int_literal(1)]),
        """$nope.jsArrayToTuple([42, 1])"""
    )


def _assert_transform(nope, expected_js, module_resolver=None):
    transformed_js = _transform_node(nope,
        module_resolver=module_resolver,
    )
    _assert_node(transformed_js, expected_js)


def _assert_node(actual, expected_js):
    if isinstance(expected_js, str):
        if isinstance(actual, list):
            actual = js.statements(actual)
        _assert_equivalent_js(expected_js, js.dumps(actual))
    else:
        assert_equal(expected_js, actual)


def _transform_node(nope, module_resolver=None):
    if module_resolver is None:
        module_resolver = FakeModuleResolver()
    
    return _transform(nope,
        module_resolver=module_resolver, 
    )
    

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


_stub_module = object()


def _assert_equivalent_js(first, second):
    assert_equal(_normalise_js(first), _normalise_js(second))


def _normalise_js(js):
    parser = slimit.parser.Parser()
    try:
        return parser.parse(js).to_ecma()
    except SyntaxError as error:
        raise SyntaxError("{}\nin:\n{}".format(error, js))


def _transform(nope_node, module_resolver):
    transformer = NodeTransformer(
        module_resolver=module_resolver,
    )
    return transformer.transform(nope_node)
