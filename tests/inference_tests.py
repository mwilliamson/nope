from nose.tools import istest, assert_equal, assert_raises

from nope import types, nodes, inference, errors
from nope.inference import infer as _infer, update_context
from nope.context import Context, new_module_context


def infer(node, context=None):
    if context is None:
        context = Context({})
    return _infer(node, context)


@istest
def can_infer_type_of_none():
    assert_equal(types.none_type, infer(nodes.none()))


@istest
def can_infer_type_of_int_literal():
    assert_equal(types.int_type, infer(nodes.int("4")))


@istest
def can_infer_type_of_str_literal():
    assert_equal(types.str_type, infer(nodes.str("!")))


@istest
def can_infer_type_of_variable_reference():
    assert_equal(types.int_type, infer(nodes.ref("x"), Context({"x": types.int_type})))


@istest
def can_infer_type_of_list_of_ints():
    assert_equal(types.list_type(types.int_type), infer(nodes.list([nodes.int(1), nodes.int(42)])))


@istest
def can_infer_type_of_call():
    context = Context({"f": types.func([types.str_type], types.int_type)})
    assert_equal(types.int_type, infer(nodes.call(nodes.ref("f"), [nodes.str("")]), context))


@istest
def call_arguments_must_match():
    context = Context({"f": types.func([types.str_type], types.int_type)})
    arg_node = nodes.int(4)
    node = nodes.call(nodes.ref("f"), [arg_node])
    _assert_type_mismatch(
        lambda: infer(node, context),
        expected=types.str_type,
        actual=types.int_type,
        node=arg_node,
    )


@istest
def call_arguments_length_must_match():
    context = Context({"f": types.func([types.str_type], types.int_type)})
    node = nodes.call(nodes.ref("f"), [])
    try:
        infer(node, context)
        assert False, "Expected error"
    except errors.ArgumentsLengthError as error:
        assert_equal(1, error.expected)
        assert_equal(0, error.actual)
        assert error.node is node


@istest
def can_infer_type_of_attribute():
    context = Context({"x": types.str_type})
    assert_equal(
        types.func([types.str_type], types.int_type),
        infer(nodes.attr(nodes.ref("x"), "find"), context)
    )


@istest
def type_error_if_attribute_does_not_exist():
    context = Context({"x": types.str_type})
    node = nodes.attr(nodes.ref("x"), "swizzlify")
    try:
        infer(node, context)
        assert False, "Expected error"
    except errors.AttributeError as error:
        assert_equal("str object has no attribute swizzlify", str(error))
        assert error.node is node
    

@istest
def can_infer_type_of_function_with_no_args_and_no_return():
    node = nodes.func("f", args=nodes.Arguments([]), return_annotation=None, body=[])
    assert_equal(types.func([], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_args_and_no_return():
    args = nodes.arguments([
        nodes.argument("x", nodes.ref("int")),
        nodes.argument("y", nodes.ref("str")),
    ])
    node = nodes.func("f", args=args, return_annotation=None, body=[])
    assert_equal(types.func([types.int_type, types.str_type], types.none_type), _infer_func_type(node))


@istest
def can_infer_type_of_function_with_no_args_and_return_annotation():
    node = nodes.func(
        "f",
        args=nodes.Arguments([]),
        return_annotation=nodes.ref("int"),
        body=[
            nodes.ret(nodes.int(4))
        ]
    )
    assert_equal(types.func([], types.int_type), _infer_func_type(node))


@istest
def type_mismatch_if_return_type_is_incorrect():
    return_node = nodes.ret(nodes.str("!"))
    node = nodes.func(
        "f",
        args=nodes.arguments([]),
        return_annotation=nodes.ref("int"),
        body=[return_node],
    )
    _assert_type_mismatch(lambda: _infer_func_type(node), expected=types.int_type, actual=types.str_type, node=return_node)


@istest
def function_adds_arguments_to_context():
    args = nodes.arguments([
        nodes.argument("x", nodes.ref("int")),
    ])
    body = [nodes.ret(nodes.ref("x"))]
    node = nodes.func("f", args=args, return_annotation=nodes.ref("int"), body=body)
    assert_equal(types.func([types.int_type], types.int_type), _infer_func_type(node))


@istest
def assignment_adds_variable_to_context():
    node = nodes.assign(["x"], nodes.int(1))
    context = Context({})
    update_context(node, context)
    assert_equal(types.int_type, context.lookup("x"))


@istest
def variables_are_shadowed_in_defs():
    node = nodes.func("g", nodes.args([]), None, [
        nodes.assign(["x"], nodes.str("Hello")),
        nodes.expression_statement(nodes.call(nodes.ref("f"), [nodes.ref("x")])),
    ])
    
    context = Context({
        "f": types.func([types.str_type], types.none_type),
        "x": types.int_type,
    })
    update_context(node, context)
    
    assert_equal(types.int_type, context.lookup("x"))


@istest
def local_variables_cannot_be_used_before_assigned():
    usage_node = nodes.ref("x")
    node = nodes.func("g", nodes.args([]), None, [
        nodes.expression_statement(nodes.call(nodes.ref("f"), [usage_node])),
        nodes.assign("x", nodes.str("Hello")),
    ])
    
    context = Context({
        "f": types.func([types.str_type], types.none_type),
        "x": types.int_type,
    })
    try:
        update_context(node, context)
        assert False, "Expected UnboundLocalError"
    except errors.UnboundLocalError as error:
        assert_equal("local variable x referenced before assignment", str(error))
        assert error.node is usage_node


@istest
def module_exports_are_specified_using_all():
    module_node = nodes.module([
        nodes.assign(["__all__"], nodes.list([nodes.str("x"), nodes.str("z")])),
        nodes.assign(["x"], nodes.str("one")),
        nodes.assign(["y"], nodes.str("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    context = Context({})
    module = inference.check(module_node)
    assert_equal(types.str_type, module.attrs["x"])
    assert_raises(KeyError, lambda: module.attrs["y"])
    assert_equal(types.int_type, module.attrs["z"])


@istest
def module_exports_default_to_values_without_leading_underscore_if_all_is_not_specified():
    module_node = nodes.module([
        nodes.assign(["x"], nodes.str("one")),
        nodes.assign(["_y"], nodes.str("two")),
        nodes.assign(["z"], nodes.int(3)),
    ])
    
    context = Context({})
    module = inference.check(module_node)
    assert_equal(types.str_type, module.attrs["x"])
    assert_raises(KeyError, lambda: module.attrs["_y"])
    assert_equal(types.int_type, module.attrs["z"])


@istest
def can_import_local_module_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message.py": types.Module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree, module_path="root/main.py", is_executable=True)
    
    assert_equal(types.str_type, context.lookup("message").attrs["value"])


@istest
def can_import_local_package_using_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": types.Module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree, module_path="root/main.py", is_executable=True)
    
    assert_equal(types.str_type, context.lookup("message").attrs["value"])


@istest
def can_use_aliases_with_plain_import_syntax():
    node = nodes.Import([nodes.import_alias("message", "m")])
    
    source_tree = FakeSourceTree({
        "root/message.py": types.Module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree, module_path="root/main.py", is_executable=True)
    
    assert_equal(types.str_type, context.lookup("m").attrs["value"])
    assert_raises(KeyError, lambda: context.lookup("message"))


@istest
def cannot_import_local_packages_if_not_in_executable():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": types.Module({"value": types.str_type})
    })
    
    try:
        _update_blank_context(node, source_tree, module_path="root/main.py", is_executable=False)
        assert False, "Expected error"
    except errors.ImportError as error:
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_is_ambiguous():
    node = nodes.Import([nodes.import_alias("message", None)])
    
    source_tree = FakeSourceTree({
        "root/message/__init__.py": types.Module({"value": types.str_type}),
        "root/message.py": types.Module({"value": types.str_type})
    })
    
    try:
        _update_blank_context(node, source_tree, module_path="root/main.py", is_executable=True)
        assert False
    except errors.ImportError as error:
        assert_equal("Import is ambiguous: the module 'message.py' and the package 'message/__init__.py' both exist", str(error))
        assert_equal(node, error.node)


@istest
def error_is_raised_if_import_cannot_be_resolved():
    node = nodes.Import([nodes.import_alias("message.value", None)])
    source_tree = FakeSourceTree({})
    
    try:
        _update_blank_context(node, source_tree, module_path="root/main.py", is_executable=True)
        assert False
    except errors.ImportError as error:
        assert_equal("Could not find module 'message.value'", str(error))
        assert_equal(node, error.node)


@istest
def can_import_relative_module_using_import_from_syntax():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", None)])
    
    source_tree = FakeSourceTree({
        "root/message.py": types.Module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree, module_path="root/main.py")
    
    assert_equal(types.str_type, context.lookup("value"))
    assert_raises(KeyError, lambda: context.lookup("message"))


@istest
def can_import_relative_module_using_import_from_syntax_with_alias():
    node = nodes.import_from([".", "message"], [nodes.import_alias("value", "v")])
    
    source_tree = FakeSourceTree({
        "root/message.py": types.Module({"value": types.str_type})
    })
    
    context = _update_blank_context(node, source_tree, module_path="root/main.py")
    
    assert_equal(types.str_type, context.lookup("v"))
    assert_raises(KeyError, lambda: context.lookup("value"))
    assert_raises(KeyError, lambda: context.lookup("message"))


class FakeSourceTree(object):
    def __init__(self, modules):
        self._modules = modules
    
    def check(self, path):
        return self._modules.get(path)


def _infer_func_type(func_node):
    context = new_module_context()
    update_context(func_node, context)
    return context.lookup(func_node.name)


def _update_blank_context(node, *args, **kwargs):
    context = Context({})
    update_context(node, context, *args, **kwargs)
    return context


def _assert_type_mismatch(func, expected, actual, node):
    try:
        func()
        assert False, "Expected type mismatch"
    except errors.TypeMismatchError as mismatch:
        assert_equal(expected, mismatch.expected)
        assert_equal(actual, mismatch.actual)
        assert mismatch.node is node
