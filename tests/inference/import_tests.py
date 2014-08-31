from nose.tools import istest, assert_equal, assert_raises

from nope import types, nodes, errors
from .util import FakeModuleTypes, update_blank_context, module


@istest
def can_import_local_module_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeModuleTypes({
        "root/message.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True)
    
    assert_equal(types.str_type, context.lookup_name("message").attrs.type_of("value"))


@istest
def can_import_local_package_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeModuleTypes({
        "root/message/__init__.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True)
    
    assert_equal(types.str_type, context.lookup_name("message").attrs.type_of("value"))


@istest
def importing_module_in_package_mutates_that_package():
    node = nodes.Import([nodes.import_alias("messages.hello", None)])
    messagesmodule = module([])
    hellomodule = module([types.attr("value", types.str_type)])
    
    source_tree = FakeModuleTypes({
        "root/messages/__init__.py": messagesmodule,
        "root/messages/hello.py": hellomodule,
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True)
    
    assert_equal(hellomodule, context.lookup_name("messages").attrs.type_of("hello"))


@istest
def can_use_aliases_with_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", "m")])
    
    source_tree = FakeModuleTypes({
        "root/message.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True)
    
    assert_equal(types.str_type, context.lookup_name("m").attrs.type_of("value"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("message"))


@istest
def cannot_import_local_packages_if_not_in_executable():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeModuleTypes({
        "root/message/__init__.py": module([types.attr("value", types.str_type)]),
    })
    
    try:
        update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=False)
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_is_ambiguous():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeModuleTypes({
        "root/message/__init__.py": module([types.attr("value", types.str_type)]),
        "root/message.py": module([types.attr("value", types.str_type)]),
    })
    
    try:
        update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=True)
        assert False
    except errors.ImportError as error:
        assert_equal("Import is ambiguous: the module 'message.py' and the package 'message/__init__.py' both exist", str(error))
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_cannot_be_resolved():
    node = nodes.Import([nodes.import_alias("message.value", None)])
    source_tree = FakeModuleTypes({
        "root/message/__init__.py": module([]),
    })
    
    try:
        update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=True)
        assert False
    except errors.ImportError as error:
        assert_equal("Could not find module 'message.value'", str(error))
        assert_equal(node, error.node)


@istest
def can_import_value_from_relative_module_using_import_from_syntax():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", None)])
    
    source_tree = FakeModuleTypes({
        "root/message.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py")
    
    assert_equal(types.str_type, context.lookup_name("value"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("message"))


@istest
def can_import_relative_module_using_import_from_syntax():
    node = nodes.import_from(["."], [nodes.import_alias("message", None)])
    rootmodule = module([])
    messagemodule = module([types.attr("value", types.str_type)])
    
    source_tree = FakeModuleTypes({
        "root/__init__.py": rootmodule,
        "root/message.py": messagemodule,
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py")
    
    assert_equal(types.str_type, context.lookup_name("message").attrs.type_of("value"))
    assert_equal(messagemodule, rootmodule.attrs.type_of("message"))


@istest
def can_import_relative_module_using_import_from_syntax_with_alias():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", "v")])
    
    source_tree = FakeModuleTypes({
        "root/message.py": module([types.attr("value", types.str_type)]),
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py")
    
    assert_equal(types.str_type, context.lookup_name("v"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("value"))
    assert_raises(errors.UnboundLocalError, lambda: context.lookup_name("message"))
