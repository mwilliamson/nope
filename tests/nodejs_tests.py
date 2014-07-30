from nose.tools import istest, assert_equal

from nope import nodejs, nodes, js


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
            nodes.assign(["__all__"], nodes.list([nodes.str("x")]))
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
                    js.property_access(js.ref("$nope.exports"), "x"),
                    js.ref("x"),
                )
            ),
        ])
    )


@istest
def test_transform_import_from_current_package():
    _assert_transform(
        nodes.import_from(["."], [nodes.import_alias("x", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$nope.require"), [js.string("./")])),
            js.var("x", js.property_access(js.ref("$import0"), "x")),
        ])
    )


@istest
def test_transform_import_from_parent_package():
    _assert_transform(
        nodes.import_from([".."], [nodes.import_alias("x", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$nope.require"), [js.string("../")])),
            js.var("x", js.property_access(js.ref("$import0"), "x")),
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
            js.var("$import0", js.call(js.ref("$nope.require"), [js.string("./")])),
            js.var("x", js.property_access(js.ref("$import0"), "x")),
            js.var("y", js.property_access(js.ref("$import0"), "y")),
        ])
    )


@istest
def test_transform_import_from_with_alias():
    _assert_transform(
        nodes.import_from(["."], [
            nodes.import_alias("x", "y"),
        ]),
        js.statements([
            js.var("$import0", js.call(js.ref("$nope.require"), [js.string("./")])),
            js.var("y", js.property_access(js.ref("$import0"), "x")),
        ])
    )


@istest
def test_transform_import_from_child_package():
    _assert_transform(
        nodes.import_from([".", "x"], [nodes.import_alias("y", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$nope.require"), [js.string("./x")])),
            js.var("y", js.property_access(js.ref("$import0"), "y")),
        ])
    )


@istest
def test_transform_import_from_absolute_package():
    _assert_transform(
        nodes.import_from(["x"], [nodes.import_alias("y", None)]),
        js.statements([
            js.var("$import0", js.call(js.ref("$nope.require"), [js.string("x")])),
            js.var("y", js.property_access(js.ref("$import0"), "y")),
        ])
    )


@istest
def test_multiple_imports_use_different_names():
    _assert_transform(
        nodes.module([
            nodes.import_from([".", "x1"], [nodes.import_alias("y1", None)]),
            nodes.import_from([".", "x2"], [nodes.import_alias("y2", None)]),
        ]),
        js.statements([
            js.statements([
                js.var("$import0", js.call(js.ref("$nope.require"), [js.string("./x1")])),
                js.var("y1", js.property_access(js.ref("$import0"), "y1")),
            ]),
            js.statements([
                js.var("$import1", js.call(js.ref("$nope.require"), [js.string("./x2")])),
                js.var("y2", js.property_access(js.ref("$import1"), "y2")),
            ]),
        ])
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
def test_transform_compound_assignments():
    _assert_transform(
        nodes.assign(["x", "y"], nodes.ref("z")),
        js.expression_statement(js.assign("x", js.assign("y", js.ref("z")))),
    )


@istest
def test_transform_return():
    _assert_transform(
        nodes.ret(nodes.ref("x")),
        js.ret(js.ref("x"))
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
def test_transform_string_expression():
    _assert_transform(
        nodes.str("hello"),
        js.string("hello")
    )


@istest
def test_transform_int_expression():
    _assert_transform(
        nodes.int(42),
        js.number(42)
    )
    

def _assert_transform(nope, js):
    assert_equal(js, nodejs.transform(nope))