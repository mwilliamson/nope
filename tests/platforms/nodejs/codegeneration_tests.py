from nose.tools import istest, assert_equal

from nope.platforms.nodejs import codegeneration, js
from nope import nodes, types


@istest
def test_transform_module():
    _assert_transform(
        nodes.module([nodes.expression_statement(nodes.ref("x"))]),
        js.statements([js.expression_statement(js.ref("x"))])
    )


@istest
def test_transform_module_with_exports():
    _assert_transform(
        nodes.module([
            nodes.assign(["__all__"], nodes.list([nodes.string("x")]))
        ]),
        js.statements([
            js.var("__all__"),
            js.expression_statement(
                js.assign(
                    "__all__",
                    js.array([js.string("x")])
                )
            ),
            js.expression_statement(
                js.assign(
                    js.property_access(js.ref("$exports"), "x"),
                    js.ref("x"),
                )
            ),
        ])
    )


@istest
def test_transform_basic_import_of_top_level_module():
    _assert_transform(
        nodes.Import([nodes.import_alias("x", None)]),
        js.statements([
            js.assign_statement("x", js.call(js.ref("$require"), [js.string("x")])),
        ])
    )


@istest
def test_transform_basic_import_of_module_in_package():
    _assert_transform(
        nodes.Import([nodes.import_alias("x.y", None)]),
        js.statements([
            js.assign_statement("x", js.call(js.ref("$require"), [js.string("x")])),
            js.assign_statement(js.property_access(js.ref("x"), "y"), js.call(js.ref("$require"), [js.string("x/y")])),
        ])
    )


@istest
def test_transform_import_from_current_package():
    _assert_transform(
        nodes.import_from(["."], [nodes.import_alias("x", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$require"), [js.string("./")])),
            js.assign_statement("x", js.property_access(js.ref("$import0"), "x")),
        ])
    )


@istest
def test_transform_import_from_parent_package():
    _assert_transform(
        nodes.import_from([".."], [nodes.import_alias("x", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$require"), [js.string("../")])),
            js.assign_statement("x", js.property_access(js.ref("$import0"), "x")),
        ])
    )


@istest
def test_transform_import_from_with_multiple_names():
    _assert_transform(
        nodes.import_from(["."], [
            nodes.import_alias("x", None),
            nodes.import_alias("y", None),
        ]),
        js.statements([
            js.var("$import0", js.call(js.ref("$require"), [js.string("./")])),
            js.assign_statement("x", js.property_access(js.ref("$import0"), "x")),
            js.assign_statement("y", js.property_access(js.ref("$import0"), "y")),
        ])
    )


@istest
def test_transform_import_from_with_alias():
    _assert_transform(
        nodes.import_from(["."], [
            nodes.import_alias("x", "y"),
        ]),
        js.statements([
            js.var("$import0", js.call(js.ref("$require"), [js.string("./")])),
            js.assign_statement("y", js.property_access(js.ref("$import0"), "x")),
        ])
    )


@istest
def test_transform_import_from_child_package():
    _assert_transform(
        nodes.import_from([".", "x"], [nodes.import_alias("y", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$require"), [js.string("./x")])),
            js.assign_statement("y", js.property_access(js.ref("$import0"), "y")),
        ])
    )


@istest
def test_transform_import_from_absolute_package():
    _assert_transform(
        nodes.import_from(["x"], [nodes.import_alias("y", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$require"), [js.string("x")])),
            js.assign_statement("y", js.property_access(js.ref("$import0"), "y")),
        ])
    )


@istest
def test_multiple_imports_use_different_names():
    assert_equal(
        codegeneration.transform(nodes.module([
            nodes.import_from([".", "x1"], [nodes.import_alias("y1", None)]),
            nodes.import_from([".", "x2"], [nodes.import_alias("y2", None)]),
        ]), type_lookup=types.TypeLookup({})).statements[:4],
        [
            js.var("y1"),
            js.var("y2"),
            js.statements([
                js.var("$import0", js.call(js.ref("$require"), [js.string("./x1")])),
                js.assign_statement("y1", js.property_access(js.ref("$import0"), "y1")),
            ]),
            js.statements([
                js.var("$import1", js.call(js.ref("$require"), [js.string("./x2")])),
                js.assign_statement("y2", js.property_access(js.ref("$import1"), "y2")),
            ]),
        ],
    )


@istest
def test_transform_expression_statement():
    _assert_transform(
        nodes.expression_statement(nodes.ref("x")),
        js.expression_statement(js.ref("x"))
    )


@istest
def test_transform_function_declaration():
    _assert_transform(
        nodes.func(
            name="f",
            args=nodes.args([nodes.arg("x", None), nodes.arg("y", None)]),
            return_annotation=None,
            body=[nodes.ret(nodes.ref("x"))],
        ),
        js.function_declaration(
            name="f",
            args=["x", "y"],
            body=[js.ret(js.ref("x"))],
        )
    )


@istest
def test_transform_function_declaration_declares_variables_at_top_of_function():
    _assert_transform(
        nodes.func(
            name="f",
            args=nodes.args([]),
            return_annotation=None,
            body=[nodes.assign(["x"], nodes.ref("y"))],
        ),
        js.function_declaration(
            name="f",
            args=[],
            body=[
                js.var("x"),
                js.expression_statement(js.assign("x", js.ref("y"))),
            ],
        )
    )


@istest
def test_transform_single_assignment():
    _assert_transform(
        nodes.assign(["x"], nodes.ref("z")),
        js.expression_statement(js.assign("x", js.ref("z"))),
    )


@istest
def test_transform_compound_assignments():
    _assert_transform(
        nodes.assign(["x", "y"], nodes.ref("z")),
        js.statements([
            js.var("$tmp0", js.ref("z")),
            js.assign_statement("x", js.ref("$tmp0")),
            js.assign_statement("y", js.ref("$tmp0")),
        ]),
    )


@istest
def test_transform_return():
    _assert_transform(
        nodes.ret(nodes.ref("x")),
        js.ret(js.ref("x"))
    )


@istest
def test_transform_if_else():
    _assert_transform(
        nodes.if_else(
            nodes.ref("x"),
            [nodes.ret(nodes.ref("y"))],
            [nodes.ret(nodes.ref("z"))],
        ),
        js.if_else(
            js.call(js.ref("$nope.builtins.bool"), [js.ref("x")]),
            [js.ret(js.ref("y"))],
            [js.ret(js.ref("z"))],
        )
    )


@istest
def test_transform_call():
    _assert_transform(
        nodes.call(nodes.ref("f"), [nodes.ref("x"), nodes.ref("y")]),
        js.call(js.ref("f"), [js.ref("x"), js.ref("y")])
    )


@istest
def test_transform_property_access():
    _assert_transform(
        nodes.attr(nodes.ref("x"), "y"),
        js.call(js.ref("$nope.propertyAccess"), [js.ref("x"), js.string("y")])
    )


@istest
def test_transform_getitem_subscript():
    _assert_transform(
        nodes.subscript(nodes.ref("x"), nodes.ref("y")),
        js.call(js.ref("$nope.operators.getitem"), [js.ref("x"), js.ref("y")])
    )


@istest
def test_transform_setitem_subscript():
    _assert_transform(
        nodes.assign([nodes.subscript(nodes.ref("x"), nodes.ref("y"))], nodes.ref("z")),
        js.expression_statement(js.call(js.ref("$nope.operators.setitem"), [js.ref("x"), js.ref("y"), js.ref("z")]))
    )


@istest
def test_transform_binary_operation():
    _assert_transform(
        nodes.add(nodes.ref("x"), nodes.ref("y")),
        js.call(js.ref("$nope.operators.add"), [js.ref("x"), js.ref("y")])
    )


@istest
def test_normal_js_addition_is_used_if_both_operands_are_ints():
    left = nodes.ref("x")
    right = nodes.ref("y")
    
    type_lookup = types.TypeLookup({
        id(left): types.int_type,
        id(right): types.int_type,
    })
    
    _assert_transform(
        nodes.add(left, right),
        js.binary_operation("+", js.ref("x"), js.ref("y")),
        type_lookup=type_lookup,
    )


@istest
def test_normal_binary_operation_if_only_one_side_is_int():
    x = nodes.ref("x")
    y = nodes.ref("y")
    
    type_lookup = types.TypeLookup({
        id(x): types.int_type,
        id(y): types.object_type,
    })
    
    _assert_transform(
        nodes.add(x, y),
        js.call(js.ref("$nope.operators.add"), [js.ref("x"), js.ref("y")]),
        type_lookup=type_lookup,
    )
    
    _assert_transform(
        nodes.add(y, x),
        js.call(js.ref("$nope.operators.add"), [js.ref("y"), js.ref("x")]),
        type_lookup=type_lookup,
    )


@istest
def test_transform_unary_operation():
    _assert_transform(
        nodes.neg(nodes.ref("x")),
        js.call(js.ref("$nope.operators.neg"), [js.ref("x")])
    )


@istest
def test_normal_javascript_negation_is_used_if_operand_is_int():
    x = nodes.ref("x")
    
    type_lookup = types.TypeLookup({
        id(x): types.int_type,
    })
    
    _assert_transform(
        nodes.neg(x),
        js.unary_operation("-", js.ref("x")),
        type_lookup=type_lookup,
    )


@istest
def test_transform_variable_reference():
    _assert_transform(
        nodes.ref("x"),
        js.ref("x")
    )


@istest
def test_transform_none_expression():
    _assert_transform(
        nodes.none(),
        js.null
    )


@istest
def test_transform_boolean_expression():
    _assert_transform(
        nodes.boolean(True),
        js.boolean(True)
    )
    _assert_transform(
        nodes.boolean(False),
        js.boolean(False)
    )


@istest
def test_transform_string_expression():
    _assert_transform(
        nodes.string("hello"),
        js.string("hello")
    )


@istest
def test_transform_int_expression():
    _assert_transform(
        nodes.int(42),
        js.number(42)
    )
    

def _assert_transform(nope, js, type_lookup=None):
    if type_lookup is None:
        type_lookup = types.TypeLookup({})
    
    assert_equal(js, codegeneration.transform(nope, type_lookup))
