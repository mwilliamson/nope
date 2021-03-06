import os

from nose.tools import istest, assert_equal, assert_in

from nope import couscous as cc
from nope.platforms.dotnet import cs
from nope.platforms.dotnet.codegeneration import Transformer
from nope.modules import LocalModule, BuiltinModule
from ...testing import wip

# TODO: put this hack somewhere neater
import unittest
unittest.TestCase.maxDiff = None


@istest
class ModuleTests(object):
    @istest
    def executable_module_is_converted_to_class_with_main_method(self):
        node = cc.module([
            cc.expression_statement(cc.call(cc.ref("f"), []))
        ], is_executable=True)
        module = LocalModule("blah.py", node)
        
        expected = """internal class Program {
    internal static void Main() {
        f();
    }
}
"""
        assert_equal(expected, cs.dumps(transform(module)))

    @istest
    def auxiliary_definitions_are_included_in_module(self):
        node = cc.module([cc.class_("A", methods=[], body=[])], is_executable=True)
        module = LocalModule("blah.py", node)
        
        assert_in("class __A", cs.dumps(transform(module)))
    
    @istest
    def non_executable_module_adds_value_to_modules_object(self):
        node = cc.module([], is_executable=False, exported_names=["x"])
        module = LocalModule("blah.py", node)
        
        expected = """internal class Module__blah_py {
    internal static dynamic Init() {
        dynamic __module = new System.Dynamic.ExpandoObject();
        __module.x = x;
        return __module;
    }
}
"""
        assert_equal(expected, cs.dumps(transform(module)))


@istest
class ModuleReferenceTests(object):
    @istest
    def absolute_module_reference_is_translated_to_get_module_with_reference_to_module_class(self):
        module_resolver = FakeModuleResolver({
            ("os", "path"): LocalModule("blah.py", None),
        })
        node = cc.module_ref(["os", "path"])
        
        expected = """__Nope.Internals.@Import(Module__blah_py.Init)"""
        assert_equal(expected, cs.dumps(transform(node, module_resolver=module_resolver)))
    
    
    @istest
    def path_is_normalised_before_hashing(self):
        module_resolver = FakeModuleResolver({
            ("os", "path"): LocalModule("x/../blah.py", None),
        })
        node = cc.module_ref(["os", "path"])
        
        expected = """__Nope.Internals.@Import(Module__blah_py.Init)"""
        assert_equal(expected, cs.dumps(transform(node, module_resolver=module_resolver)))
    

@istest
class FunctionDefinitionTests(object):
    @istest
    def function_with_zero_arguments_is_converted_to_csharp_lambda_assignment(self):
        node = cc.func("f", [], [cc.ret(cc.none)])
        
        expected = """
f = ((System.Func<dynamic>)(() =>
{
    return __NopeNone.Value;
}));"""
        assert_equal(expected.strip(), cs.dumps(transform(node)).strip())
        
    @istest
    def function_with_multiple_arguments_is_converted_to_csharp_lambda_assignment_with_dynamic_args(self):
        node = cc.func("f", [cc.arg("x"), cc.arg("y")], [cc.ret(cc.none)])
        
        expected = """
f = ((System.Func<dynamic, dynamic, dynamic>)((dynamic x, dynamic y) =>
{
    return __NopeNone.Value;
}));"""
        assert_equal(expected.strip(), cs.dumps(transform(node)).strip())


@istest
class RaiseStatementTests(object):
    @istest
    def raise_generates_throw_with_nope_exception_contained_in_csharp_exception(self):
        node = cc.raise_(cc.ref("x"))
        
        expected = """throw __Nope.Internals.@CreateException(x);
"""
        assert_equal(expected, cs.dumps(transform(node)))


@istest
class TryStatementTests(object):
    @istest
    def try_with_finally_is_converted_to_try_with_finally(self):
        node = cc.try_(
            [cc.ret(cc.ref("x"))],
            finally_body=[cc.expression_statement(cc.ref("y"))]
        )
        
        expected = """try {
    return x;
} finally {
    y;
}
"""
        assert_equal(expected, cs.dumps(transform(node)))


    @istest
    def except_handler_is_converted_to_catch_for_nope_exceptions(self):
        node = cc.try_(
            [],
            handlers=[cc.except_(None, None, [cc.expression_statement(cc.ref("y"))])]
        )
        
        expected = """try {
} catch (__Nope.Internals.@__NopeException __exception) {
    y;
}
"""
        assert_equal(expected, cs.dumps(transform(node)))


    @istest
    def type_of_nope_exception_is_checked_if_handler_has_exception_type(self):
        node = cc.try_(
            [],
            handlers=[
                cc.except_(cc.ref("Exception"), None, [
                    cc.ret(cc.ref("value"))
                ])
            ]
        )
        
        expected = """try {
} catch (__Nope.Internals.@__NopeException __exception) {
    if ((__Nope.Builtins.@isinstance(__exception.__Value, Exception)).__Value) {
        return value;
    } else {
        throw;
    }
}
"""
        assert_equal(expected, cs.dumps(transform(node)))


    @istest
    def handlers_are_converted_to_if_statements_in_order(self):
        node = cc.try_(
            [],
            handlers=[
                cc.except_(cc.ref("AssertionError"), None, []),
                cc.except_(cc.ref("Exception"), None, []),
            ]
        )
        
        expected = """try {
} catch (__Nope.Internals.@__NopeException __exception) {
    if ((__Nope.Builtins.@isinstance(__exception.__Value, AssertionError)).__Value) {
    } else {
        if ((__Nope.Builtins.@isinstance(__exception.__Value, Exception)).__Value) {
        } else {
            throw;
        }
    }
}
"""
        assert_equal(expected, cs.dumps(transform(node)))


    @istest
    def nope_exception_is_extracted_from_dotnet_exception_if_exception_is_named_in_catch(self):
        node = cc.try_(
            [],
            handlers=[
                cc.except_(cc.ref("Exception"), cc.ref("error"), [
                    cc.ret(cc.ref("error"))
                ])
            ]
        )
        
        expected = """try {
} catch (__Nope.Internals.@__NopeException __exception) {
    if ((__Nope.Builtins.@isinstance(__exception.__Value, Exception)).__Value) {
        error = __exception.__Value;
        return error;
    } else {
        throw;
    }
}
"""
        assert_equal(expected, cs.dumps(transform(node)))


@istest
class ClassDefinitionTests(object):
    @istest
    def class_definition_creates_object_with_call_method_for_init(self):
        node = cc.class_("A", methods=[], body=[])
        
        expected_aux = """internal class __A {
}
"""
        
        expected = """A = new
{
    __call__ = ((System.Func<dynamic>)(() =>
    {
        dynamic __self = null;
        __self = new __A();
        return __self;
    })),
};
"""
        transformer = _create_transformer()
        assert_equal(expected, cs.dumps(transformer.transform(node)))
        assert_equal(expected_aux, cs.dumps(transformer.aux()))
    
    @istest
    def methods_are_set_as_members_on_object(self):
        node = cc.class_("A", methods=[
            cc.func("f", [cc.arg("self")], [
                cc.ret(cc.ref("self"))
            ])
        ], body=[])
        
        expected_aux = """internal class __A {
    internal dynamic f;
}
"""

        expected = """A = new
{
    __call__ = ((System.Func<dynamic>)(() =>
    {
        dynamic __self = null;
        __self = new __A {
            f = ((System.Func<dynamic>)(() =>
            {
                dynamic self = __self;
                return self;
            })),
        };
        return __self;
    })),
};
"""
        transformer = _create_transformer()
        assert_equal(expected, cs.dumps(transformer.transform(node)))
        assert_equal(expected_aux, cs.dumps(transformer.aux()))
    
    @istest
    def init_method_is_called_if_present(self):
        node = cc.class_("A", methods=[
            cc.func("__init__", [cc.arg("self"), cc.arg("value")], [
                cc.expression_statement(cc.call(cc.ref("print"), [cc.ref("value")]))
            ])
        ], body=[])
        expected_aux = """internal class __A {
    internal dynamic __init__;
}
"""

        expected = """A = new
{
    __call__ = ((System.Func<dynamic, dynamic>)((dynamic __value) =>
    {
        dynamic __self = null;
        __self = new __A {
            __init__ = ((System.Func<dynamic, dynamic>)((dynamic value) =>
            {
                dynamic self = __self;
                print(value);
            })),
        };
        __self.__init__(__value);
        return __self;
    })),
};
"""
        transformer = _create_transformer()
        assert_equal(expected, cs.dumps(transformer.transform(node)))
        assert_equal(expected_aux, cs.dumps(transformer.aux()))


def transform(node, module_resolver=None):
    return _create_transformer(module_resolver).transform(node)

def _create_transformer(module_resolver=None):
    return Transformer(
        module_resolver=module_resolver,
        prelude="",
        path_hash=lambda path: path.replace(".", "_")
    )
    

class FakeModuleResolver(object):
    def __init__(self, imports):
        self._imports = imports
    
    def resolve_import_path(self, names):
        return self._imports[tuple(names)]


