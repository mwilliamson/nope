from nose.tools import istest, assert_equal, assert_raises

from nope import types, nodes, errors
from .util import FakeModuleTypes, FakeModuleResolver, update_blank_context, module as module_type
from nope.modules import LocalModule, BuiltinModule


@istest
def can_import_module_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    context = _update_blank_context(node, {
        ("message", ): module_type([types.attr("value", types.str_type)])
    })
    
    assert_equal(types.str_type, context.lookup_name("message").attrs.type_of("value"))


@istest
def importing_module_in_package_mutates_that_package_in_importing_module_only():
    node = nodes.Import([nodes.import_alias("messages.hello", None)])
    messages_module = module_type([])
    hello_module = module_type([types.attr("value", types.str_type)])
    
    context = _update_blank_context(node, {
        ("messages", ): messages_module,
        ("messages", "hello"): hello_module,
    })
    
    assert_equal(types.str_type, context.lookup_name("messages").attrs.type_of("hello").attrs.type_of("value"))
    assert "hello" not in messages_module.attrs


@istest
def can_import_module_after_importing_parent_package():
    messages_module = module_type([])
    hello_module = module_type([types.attr("value", types.str_type)])
    modules = {
        ("messages", ): messages_module,
        ("messages", "hello"): hello_module,
    }
    
    context = _update_blank_context([
        nodes.Import([nodes.import_alias("messages", None)]),
        nodes.Import([nodes.import_alias("messages.hello", None)])
    ], modules)
    
    assert_equal(types.str_type, context.lookup_name("messages").attrs.type_of("hello").attrs.type_of("value"))
    assert "hello" not in messages_module.attrs


@istest
def can_use_aliases_with_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", "m")])
    
    context = _update_blank_context(node, {
        ("message", ): module_type([types.attr("value", types.str_type)])
    })
    
    assert_equal(types.str_type, context.lookup_name("m").attrs.type_of("value"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("message"))


@istest
def error_is_raised_if_import_cannot_be_resolved():
    node = nodes.Import([nodes.import_alias("message.value", None)])
    
    try:
        _update_blank_context(node, {})
        assert False
    except errors.ModuleNotFoundError as error:
        assert_equal(node, error.node)


@istest
def can_import_value_from_relative_module_using_import_from_syntax():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", None)])
    
    context = _update_blank_context(node, {
        (".", "message"): module_type([types.attr("value", types.str_type)])
    })
    
    assert_equal(types.str_type, context.lookup_name("value"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("message"))


@istest
def can_import_module_using_import_from_syntax():
    node = nodes.import_from(["."], [nodes.import_alias("message", None)])
    message_module = module_type([types.attr("value", types.str_type)])
    
    context = _update_blank_context(node, {
        (".", "message"): message_module,
    })
    
    assert_equal(types.str_type, context.lookup_name("message").attrs.type_of("value"))


@istest
def can_import_module_using_import_from_syntax_with_alias():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", "v")])
    
    context = _update_blank_context(node, {
        (".", "message"): module_type([types.attr("value", types.str_type)]),
    })
    
    assert_equal(types.str_type, context.lookup_name("v"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("value"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("message"))


@istest
def builtin_modules_are_typed():
    cgi_module = BuiltinModule("cgi", types.module("cgi", [
        types.attr("escape", types.none_type),
    ]))
    node = nodes.Import([nodes.import_alias("cgi", None)])
    
    context = update_blank_context(
        node,
        module_resolver=FakeModuleResolver({("cgi",): cgi_module}),
        module_types=FakeModuleTypes({}),
    )
    
    assert_equal(types.none_type, context.lookup_name("cgi").attrs.type_of("escape"))


def _update_blank_context(node, path_to_module_types):
    modules = {}
    module_types = {}
    
    for path, module_type in path_to_module_types.items():
        other_module = LocalModule(path, nodes.module([]))
        modules[path] = other_module
        module_types[other_module] = module_type
    
    return update_blank_context(
        node,
        module_resolver=FakeModuleResolver(modules),
        module_types=FakeModuleTypes(module_types)
    )



def _create_module():
    return LocalModule(None, None)
