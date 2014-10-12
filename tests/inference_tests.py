from nose.tools import istest, assert_equal

from nope import types, nodes, inference, errors, name_declaration, name_resolution, builtins, modules
from nope.modules import LocalModule

from .inference.util import FakeModuleTypes, FakeModuleResolver, module


@istest
def check_generates_type_lookup_for_all_expressions():
    int_ref_node = nodes.ref("a")
    int_node = nodes.int(3)
    str_node = nodes.string("Hello")
    
    module_node = nodes.module([
        nodes.assign(["a"], int_node),
        nodes.func("f", nodes.args([]), [
            nodes.assign("b", int_ref_node),
            nodes.assign("c", str_node),
        ]),
    ])
    
    module, type_lookup = _check(LocalModule(None, module_node))
    assert_equal(types.int_type, type_lookup.type_of(int_node))
    assert_equal(types.int_type, type_lookup.type_of(int_ref_node))
    assert_equal(types.str_type, type_lookup.type_of(str_node))


@istest
def module_exports_are_specified_using_all():
    module_node = nodes.module([
        nodes.assign(["__all__"], nodes.list_literal([nodes.string("x"), nodes.string("z")])),
        nodes.assign(["x"], nodes.string("one")),
        nodes.assign(["y"], nodes.string("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    module, type_lookup = _check(LocalModule(None, module_node))
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
    
    module, type_lookup = _check(LocalModule(None, module_node))
    assert_equal(types.str_type, module.attrs.type_of("x"))
    assert_equal(None, module.attrs.get("_y"))
    assert_equal(types.int_type, module.attrs.type_of("z"))


@istest
def only_values_that_are_definitely_bound_are_exported():
    module_node = nodes.module([
        nodes.if_else(
            nodes.boolean(True),
            [
                nodes.assign(["x"], nodes.string("one")),
                nodes.assign(["y"], nodes.string("two")),
            ],
            [
                nodes.assign(["y"], nodes.string("three")),
            ]
        )
    ])
    
    module, type_lookup = _check(LocalModule(None, module_node))
    assert_equal(None, module.attrs.get("x"))
    assert_equal(types.str_type, module.attrs.type_of("y"))


@istest
def error_is_raised_if_value_in_package_has_same_name_as_module():
    target_node = nodes.ref("x")
    node = nodes.module([nodes.assign([target_node], nodes.int(1))], is_executable=False)
    
    try:
        _check_module(LocalModule("root/__init__.py", node), {
            (".", "x"): module({}),
        })
        assert False, "Expected error"
    except errors.ImportedValueRedeclaration as error:
        assert_equal(target_node, error.node)
        assert_equal("Cannot declare value 'x' in module scope due to child module with the same name", str(error))


@istest
def values_can_have_same_name_as_child_module_if_they_are_not_in_module_scope():
    value_node = nodes.assign([nodes.ref("x")], nodes.int(1))
    node = nodes.module([
        nodes.func("f", nodes.args([]), [value_node])
    ], is_executable=False)
    
    _check_module(LocalModule("root/__init__.py", node), {
        (".", "x"): module({}),
    })


@istest
def value_in_package_can_have_same_name_as_module_if_it_is_that_module():
    value_node = nodes.import_from(["."], [nodes.import_alias("x", None)])
    node = nodes.module([value_node], is_executable=False)
    
    _check_module(LocalModule("root/__init__.py", node), {
        (".",): module({}),
        (".", "x"): module({}),
    })

# TODO: test that name bindings are checked

def _check_module(module, path_to_module_types):
    modules = {}
    module_types = {}
    
    for path, module_type in path_to_module_types.items():
        other_module = LocalModule(path, nodes.module([]))
        modules[path] = other_module
        module_types[other_module] = module_type
    
    _check(
        module,
        module_resolver=FakeModuleResolver(modules),
        module_types=FakeModuleTypes(module_types)
    )



def _check(module, module_resolver=None, module_types=None):
    declaration_finder = name_declaration.DeclarationFinder()
    checker = inference.TypeChecker(
        declaration_finder=declaration_finder,
        name_resolver=name_resolution.NameResolver(declaration_finder, initial_declarations=builtins.declarations()),
        module_exports=modules.ModuleExports(declaration_finder),
        module_resolver=module_resolver
    )
    return checker.check_module(module, module_types)
