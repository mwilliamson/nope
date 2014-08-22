from nose.tools import istest, assert_equal, assert_raises

from nope import types, nodes, errors
from .util import FakeSourceTree, update_blank_context, module


@istest
def can_import_localmodule_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["message"])
    
    assert_equal(types.str_type, context.lookup("message").attrs.type_of("value"))


@istest
def can_import_local_package_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["message"])
    
    assert_equal(types.str_type, context.lookup("message").attrs.type_of("value"))


@istest
def importingmodule_in_package_mutates_that_package():
    node = nodes.Import([nodes.import_alias("messages.hello", None)])
    messagesmodule = module([])
    hellomodule = module([types.attr("value", types.str_type)])
    
    source_tree = FakeSourceTree({
        "root/messages/__init__.py": messagesmodule,
        "root/messages/hello.py": hellomodule,
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["messages"])
    
    assert_equal(hellomodule, context.lookup("messages").attrs.type_of("hello"))


@istest
def can_use_aliases_with_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", "m")])
    
    source_tree = FakeSourceTree({
        "root/message.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        is_executable=True,
        declared_names=["m"])
    
    assert_equal(types.str_type, context.lookup("m").attrs.type_of("value"))
    assert_raises(KeyError, lambda: context.lookup("message"))


@istest
def cannot_import_local_packages_if_not_in_executable():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": module([types.attr("value", types.str_type)]),
    })
    
    try:
        update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=False,
            declared_names=["message"])
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_is_ambiguous():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": module([types.attr("value", types.str_type)]),
        "root/message.py": module([types.attr("value", types.str_type)]),
    })
    
    try:
        update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=True,
            declared_names=["message"])
        assert False
    except errors.ImportError as error:
        assert_equal("Import is ambiguous: the module 'message.py' and the package 'message/__init__.py' both exist", str(error))
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_cannot_be_resolved():
    node = nodes.Import([nodes.import_alias("message.value", None)])
    source_tree = FakeSourceTree({
        "root/message/__init__.py": module([]),
    })
    
    try:
        update_blank_context(node, source_tree,
            module_path="root/main.py",
            is_executable=True,
            declared_names=["message"])
        assert False
    except errors.ImportError as error:
        assert_equal("Could not find module 'message.value'", str(error))
        assert_equal(node, error.node)


@istest
def can_import_value_from_relativemodule_using_import_from_syntax():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", None)])
    
    source_tree = FakeSourceTree({
        "root/message.py": module([types.attr("value", types.str_type)])
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        declared_names=["value"])
    
    assert_equal(types.str_type, context.lookup("value"))
    assert_raises(KeyError, lambda: context.lookup("message"))


@istest
def can_import_relativemodule_using_import_from_syntax():
    node = nodes.import_from(["."], [nodes.import_alias("message", None)])
    rootmodule = module([])
    messagemodule = module([types.attr("value", types.str_type)])
    
    source_tree = FakeSourceTree({
        "root/__init__.py": rootmodule,
        "root/message.py": messagemodule,
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        declared_names=["message"])
    
    assert_equal(types.str_type, context.lookup("message").attrs.type_of("value"))
    assert_equal(messagemodule, rootmodule.attrs.type_of("message"))


@istest
def can_import_relativemodule_using_import_from_syntax_with_alias():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", "v")])
    
    source_tree = FakeSourceTree({
        "root/message.py": module([types.attr("value", types.str_type)]),
    })
    
    context = update_blank_context(node, source_tree,
        module_path="root/main.py",
        declared_names=["v"])
    
    assert_equal(types.str_type, context.lookup("v"))
    assert_raises(KeyError, lambda: context.lookup("value"))
    assert_raises(KeyError, lambda: context.lookup("message"))