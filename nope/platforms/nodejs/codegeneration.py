import os
import inspect
import shutil

import zuice

from ...source import SourceTree
from ...module_resolution import ModuleResolverFactory
from ... import types, files
from .transform import transform
from . import js, operations
from ...walk import walk_tree


optimise = zuice.key("optimise")


class ModuleCodeGenerator(zuice.Base):
    _optimise = zuice.dependency(optimise)
    _module_resolver_factory = zuice.dependency(ModuleResolverFactory)
    _type_lookup_factory = zuice.dependency(types.TypeLookupFactory)
    
    def generate(self, module):
        return transform(
            module.node,
            self._type_lookup_factory.for_module(module),
            self._module_resolver_factory.for_module(module),
            optimise=self._optimise
        )


class CodeGenerator(zuice.Base):
    _module_code_generator = zuice.dependency(ModuleCodeGenerator)
    _source_tree = zuice.dependency(SourceTree)
    _module_resolver_factory = zuice.dependency(ModuleResolverFactory)
    _type_lookup_factory = zuice.dependency(types.TypeLookupFactory)
    
    def generate_files(self, source_path, destination_root):
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_root, relative_path))
        
        def handle_file(path, relative_path):
            module = self._source_tree.module(path)
            
            module_resolver = self._module_resolver_factory.for_module(module)
            destination_dir = os.path.dirname(os.path.join(destination_root, relative_path))
            
            source_filename = os.path.basename(path)
            dest_filename = _js_filename(source_filename)
            dest_path = os.path.join(destination_dir, dest_filename)
            with open(dest_path, "w") as dest_file:
                _generate_prelude(dest_file, module.node.is_executable, relative_path)
                js.dump(self._module_code_generator.generate(module), dest_file)
        
        _write_nope_js(destination_root)
        _write_builtins(destination_root)
        
        walk_tree(source_path, handle_dir, handle_file)


def _write_nope_js(destination_dir):
    nope_js_path = os.path.join(os.path.dirname(__file__), "nope.js")
    with open(os.path.join(destination_dir, "$nope.js"), "w") as dest_file:
        js.dump(_number_methods_ast(), dest_file)
        
        with open(os.path.join(nope_js_path)) as source_file:
            shutil.copyfileobj(source_file, dest_file)


def _write_builtins(destination_dir):
    builtins_path = os.path.join(os.path.dirname(__file__), "__builtins")
    files.copy_recursive(builtins_path, os.path.join(destination_dir, "__builtins"))


def _number_methods_ast():
    return js.var("numberMethods", js.obj(dict(
        ("__{}__".format(name), _generate_number_method(generate_operation))
        for name, generate_operation in operations.number.items()
    )))


def _generate_number_method(generate_operation):
    number_of_args = inspect.getargspec(generate_operation)[0]
    if len(number_of_args) == 1:
        return js.function_expression([], [
            js.ret(generate_operation(js.ref("this")))
        ])
    else:
        return js.function_expression(["right"], [
            js.ret(generate_operation(js.ref("this"), js.ref("right")))
        ])


def _js_filename(python_filename):
    if python_filename == "__init__.py":
        return "index.js"
    else:
        return _replace_extension(python_filename, "js")


def _replace_extension(filename, new_extension):
    return filename[:filename.rindex(".")] + "." + new_extension


# TODO: should probably yank this from somewhere more general since it's not specific to node.js
_builtin_names = [
    "bool", "print", "abs", "divmod", "range", "Exception", "AssertionError", "str",
]

def _generate_prelude(fileobj, is_executable, relative_path):
    relative_path = "../" * _path_depth(relative_path)
    
    fileobj.write("""var $nope = require("{}./$nope");\n""".format(relative_path));
    fileobj.write("""var $exports = exports;\n""".format(relative_path));
    if is_executable:
        fileobj.write(_main_require)
    fileobj.write("""var $require = global.$nopeRequire || require;\n""")
    
    for builtin_name in _builtin_names:
        builtin_assign = js.expression_statement(js.assign(
            builtin_name,
            js.property_access(js.ref("$nope.builtins"), builtin_name),
        ))
        js.dump(builtin_assign, fileobj)


def _path_depth(path):
    depth = -1
    while path:
        path, tail = os.path.split(path)
        depth += 1
    
    return depth
        

_main_require = """
(function() {
    if (require.main === module) {
        var originalRequire = require;
        global.$nopeRequire = function(name) {
            if (isAbsoluteImport(name)) {
                var relativeImportName = "./" + name;
                if (isValidModulePath(relativeImportName)) {
                    return $require(relativeImportName);
                }
            }
            
            return originalRequire(name);
        };
    }

    function isAbsoluteImport(name) {
        return name.indexOf(".") !== 0;
    }

    function isValidModulePath(name) {
        try {
            originalRequire.resolve(name);
            return true;
        } catch(error) {
            return false;
        }
    }
})();
"""
