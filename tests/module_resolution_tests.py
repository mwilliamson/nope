from nose.tools import istest, assert_is, assert_equal

from nope import nodes, errors, module_resolution, Module


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
        assert_equal("Absolute imports not yet implemented", str(error))


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


def _resolve_import(module, names, modules):
    return module_resolution.resolve_import(
        module,
        names,
        source_tree=FakeSourceTree(modules),
    )


def _create_module(path, is_executable=False):
    return Module(path=path, node=nodes.module([], is_executable=is_executable))


class FakeSourceTree(object):
    def __init__(self, modules):
        self._modules = dict(
            (module.path, module)
            for module in modules
        )
    
    def module(self, path):
        return self._modules.get(path)
    
    def __contains__(self, path):
        return path in self._modules
