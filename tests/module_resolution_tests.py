from nose.tools import istest, assert_is, assert_equal

from nope import nodes, errors, module_resolution, name_declaration, types
from nope.modules import LocalModule, BuiltinModule, ModuleExports


@istest
def absolute_import_in_executable_module_resolves_to_module_file_in_same_directory():
    message_module = _create_module("root/message.py")
    
    resolved_module = _resolve_import(
        _create_module("root/main.py", is_executable=True),
        ["message"],
        modules=[message_module]
    )
    
    assert_is(message_module, resolved_module)


@istest
def absolute_import_in_executable_module_resolves_to_package_in_same_directory():
    message_module = _create_module("root/message/__init__.py")
    
    resolved_module = _resolve_import(
        _create_module("root/main.py", is_executable=True),
        ["message"],
        modules=[message_module]
    )
    
    assert_is(message_module, resolved_module)


@istest
def can_import_module_in_package():
    message_module = _create_module("root/message/hello.py")
    
    resolved_module = _resolve_import(
        _create_module("root/main.py", is_executable=True),
        ["message", "hello"],
        modules=[
            _create_module("root/message/__init__.py"),
            message_module,
        ]
    )
    
    assert_is(message_module, resolved_module)


@istest
def cannot_import_local_modules_if_not_in_executable():
    message_module = _create_module("root/message.py")
    
    try:
        _resolve_import(
            _create_module("root/main.py", is_executable=False),
            ["message"],
            modules=[message_module]
        )
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal("Could not find module 'message'", str(error))


@istest
def error_is_raised_if_import_is_ambiguous():
    try:
        _resolve_import(
            _create_module("root/main.py", is_executable=True),
            ["message"],
            modules=[
                _create_module("root/message/__init__.py"),
                _create_module("root/message.py"),
            ]
        )
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal("Import is ambiguous: the module 'message.py' and the package 'message/__init__.py' both exist", str(error))


@istest
def error_is_raised_if_attempting_to_import_executable_module():
    try:
        _resolve_import(
            _create_module("root/main.py", is_executable=True),
            ["message"],
            modules=[_create_module("root/message.py", is_executable=True)],
        )
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal("Cannot import executable modules", str(error))


@istest
def error_is_raised_if_import_cannot_be_resolved():
    try:
        _resolve_import(
            _create_module("root/main.py", is_executable=True),
            ["message"],
            modules=[]
        )
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal("Could not find module 'message'", str(error))


@istest
def relative_import_using_single_dot_searches_current_directory():
    message_module = _create_module("root/message.py")
    
    resolved_module = _resolve_import(
        _create_module("root/main.py", is_executable=False),
        [".", "message"],
        modules=[message_module]
    )
    
    assert_is(message_module, resolved_module)


@istest
def relative_import_using_two_dots_searches_parent_directory():
    message_module = _create_module("message.py")
    
    resolved_module = _resolve_import(
        _create_module("root/main.py", is_executable=False),
        ["..", "message"],
        modules=[message_module]
    )
    
    assert_is(message_module, resolved_module)


@istest
def absolute_import_retrieves_standard_library_module():
    cgi_module = BuiltinModule("cgi", None)
    
    resolved_module = _resolve_import(
        _create_module("root/main.py"),
        ["cgi"],
        builtin_modules={"cgi": cgi_module}
    )
    
    assert_is(cgi_module, resolved_module)


@istest
def module_import_without_value_name_can_be_resolved():
    message_module = _create_module("root/message.py")
    
    module_resolver = _module_resolver(
        _create_module("root/main.py", is_executable=True),
        modules=[message_module]
    )
    resolved_module, attr_name = module_resolver.resolve_import_value(
        ["message"],
        None,
    )
    
    assert_is(message_module, resolved_module)
    assert_equal(None, attr_name)


@istest
def value_in_local_module_can_be_resolved():
    message_module = _create_module("root/message.py", declares=["hello"])
    
    module_resolver = _module_resolver(
        _create_module("root/main.py", is_executable=True),
        modules=[message_module]
    )
    resolved_module, attr_name = module_resolver.resolve_import_value(
        ["message"],
        "hello",
    )
    
    assert_is(message_module, resolved_module)
    assert_equal("hello", attr_name)


@istest
def value_in_builtin_module_can_be_resolved():
    cgi_module = BuiltinModule(
        "cgi",
        types.module("cgi", [types.attr("escape", types.none_type)])
    )
    
    module_resolver = _module_resolver(
        _create_module("root/main.py", is_executable=True),
        builtin_modules={"cgi": cgi_module}
    )
    resolved_module, attr_name = module_resolver.resolve_import_value(
        ["cgi"],
        "escape",
    )
    
    assert_is(cgi_module, resolved_module)
    assert_equal("escape", attr_name)


@istest
def module_in_package_is_resolved_if_package_has_no_value_with_that_name():
    message_module = _create_module("root/message/__init__.py")
    hello_module = _create_module("root/message/hello.py")
    
    module_resolver = _module_resolver(
        _create_module("root/main.py", is_executable=True),
        modules=[message_module, hello_module]
    )
    resolved_module, attr_name = module_resolver.resolve_import_value(
        ["message"],
        "hello",
    )
    
    assert_is(hello_module, resolved_module)
    assert_equal(None, attr_name)


def _resolve_import(module, names, modules=None, builtin_modules=None):
    module_resolver = _module_resolver(module, modules, builtin_modules)
    return module_resolver.resolve_import_path(names)


def _module_resolver(module, modules=None, builtin_modules=None):
    if modules is None:
        modules = []
    if builtin_modules is None:
        builtin_modules = {}
        
    source_tree = FakeSourceTree(modules)
    return module_resolution.ModuleResolver(
        source_tree,
        builtin_modules,
        ModuleExports(name_declaration.DeclarationFinder()),
        module
    )
    


def _create_module(path, is_executable=False, declares=[]):
    declarations = [
        nodes.assign([nodes.ref(name)], nodes.none())
        for name in declares
    ]
    return LocalModule(
        path=path,
        node=nodes.module(declarations, is_executable=is_executable)
    )


class FakeSourceTree(object):
    def __init__(self, modules):
        self._modules = dict(
            (module.path, module)
            for module in modules
        )
    
    def module(self, path):
        return self._modules.get(path)
