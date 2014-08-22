from nose.tools import istest, assert_equal

from nope import types, nodes, inference, errors

from .inference.util import FakeSourceTree, module


@istest
def check_generates_type_lookup_for_all_expressions():
    int_ref_node = nodes.ref("a")
    int_node = nodes.int(3)
    str_node = nodes.string("Hello")
    
    module_node = nodes.module([
        nodes.assign(["a"], int_node),
        nodes.func("f", nodes.signature(), nodes.args([]), [
            nodes.assign("b", int_ref_node),
            nodes.assign("c", str_node),
        ]),
    ])
    
    module, type_lookup = inference.check(module_node)
    assert_equal(types.int_type, type_lookup.type_of(int_node))
    assert_equal(types.int_type, type_lookup.type_of(int_ref_node))
    assert_equal(types.str_type, type_lookup.type_of(str_node))


@istest
def module_exports_are_specified_using_all():
    module_node = nodes.module([
        nodes.assign(["__all__"], nodes.list([nodes.string("x"), nodes.string("z")])),
        nodes.assign(["x"], nodes.string("one")),
        nodes.assign(["y"], nodes.string("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    module, type_lookup = inference.check(module_node)
    assert_equal(types.str_type, module.attrs.type_of("x"))
    assert_equal(None, module.attrs.get("y"))
    assert_equal(types.int_type, module.attrs.type_of("z"))


@istest
def module_exports_default_to_values_without_leading_underscore_if_all_is_not_specified():
    module_node = nodes.module([
        nodes.assign(["x"], nodes.string("one")),
        nodes.assign(["_y"], nodes.string("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    module, type_lookup = inference.check(module_node)
    assert_equal(types.str_type, module.attrs.type_of("x"))
    assert_equal(None, module.attrs.get("_y"))
    assert_equal(types.int_type, module.attrs.type_of("z"))




@istest
def error_is_raised_if_value_in_package_has_same_name_as_module():
    value_node = nodes.assign("x", nodes.int(1))
    node = nodes.Module([value_node], is_executable=False)
    source_tree = FakeSourceTree({
        "root/x.py": module({}),
    })
    
    try:
        inference.check(node, source_tree, module_path="root/__init__.py")
        assert False, "Expected error"
    except errors.ImportedValueRedeclaration as error:
        assert_equal(value_node, error.node)
        assert_equal("Cannot declare value 'x' in module scope due to child module with the same name", str(error))


@istest
def values_can_have_same_name_as_child_module_if_they_are_not_in_module_scope():
    value_node = nodes.assign("x", nodes.int(1))
    node = nodes.Module([
        nodes.func("f", nodes.signature(), nodes.args([]), [value_node])
    ], is_executable=False)
    source_tree = FakeSourceTree({
        "root/x.py": module({}),
    })
    
    inference.check(node, source_tree, module_path="root/__init__.py")


@istest
def value_in_package_can_have_same_name_as_module_if_it_is_that_module():
    value_node = nodes.import_from(["."], [nodes.import_alias("x", None)])
    node = nodes.Module([value_node], is_executable=False)
    source_tree = FakeSourceTree({
        "root/__init__.py": module({}),
        "root/x.py": module({}),
    })
    
    inference.check(node, source_tree, module_path="root/__init__.py")


@istest
def module_can_have_value_with_same_name_as_sibling_module():
    value_node = nodes.assign("x", nodes.int(1))
    node = nodes.Module([value_node], is_executable=False)
    source_tree = FakeSourceTree({
        "root/x.py": module([]),
    })
    
    inference.check(node, source_tree, module_path="root/y.py")
