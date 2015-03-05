import os
import inspect
import shutil

import zuice

from ... import files
from ...modules import Module
from .transform import NodeTransformer
from . import js, operations
from ...walk import walk_tree
from ...injection import CouscousTree


class CodeGenerator(zuice.Base):
    _source_tree = zuice.dependency(CouscousTree)
    _node_transformer = zuice.dependency(zuice.factory(NodeTransformer))
    
    def generate_files(self, source_path, destination_root):
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_root, relative_path))
        
        def handle_file(path, relative_path):
            self._generate_file(path, destination_root, relative_path)
        
        _write_nope_js(destination_root)
        self._write_stdlib(destination_root)
        
        walk_tree(source_path, handle_dir, handle_file)


    def _write_stdlib(self, destination_root):
        stdlib_path = os.path.join(os.path.dirname(__file__), "../../../stdlib")
        destination_stdlib_path = os.path.join(destination_root, "__stdlib")
        
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_stdlib_path, relative_path))
        
        def handle_file(path, relative_path):
            self._generate_file(path, destination_root, os.path.join("__stdlib", relative_path))
        
        walk_tree(stdlib_path, handle_dir, handle_file)
    
    def _generate_file(self, source_path, destination_root, relative_path):
        destination_dir = os.path.dirname(os.path.join(destination_root, relative_path))
        module = self._source_tree.module(source_path)
        source_filename = os.path.basename(source_path)
        dest_filename = _js_filename(source_filename)
        dest_path = os.path.join(destination_dir, dest_filename)
        with open(dest_path, "w") as dest_file:
            _generate_prelude(dest_file, module.node.is_executable, relative_path)
            node_transformer = self._node_transformer({Module: module})
            js.dump(node_transformer.transform(module.node), dest_file, pretty_print=True)
        

def _write_nope_js(destination_dir):
    nope_js_path = os.path.join(os.path.dirname(__file__), "nope.js")
    with open(os.path.join(destination_dir, "$nope.js"), "w") as dest_file:
        js.dump(_number_methods_ast(), dest_file)
        
        with open(os.path.join(nope_js_path)) as source_file:
            shutil.copyfileobj(source_file, dest_file)


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
        return files.replace_extension(python_filename, "js")


# TODO: should probably yank this from somewhere more general since it's not specific to node.js
_builtin_names = [
    "bool", "print", "abs", "divmod", "range", "Exception", "AssertionError", "StopIteration", "str", "type",
]

def _generate_prelude(fileobj, is_executable, relative_path):
    relative_path = "../" * _path_depth(relative_path)
    
    fileobj.write("""var $nope = require("{}./$nope");\n""".format(relative_path));
    fileobj.write("""var $exports = exports;\n""".format(relative_path));
    if is_executable:
        fileobj.write(_main_require)
    fileobj.write(_define_require)
    
    for builtin_name in _builtin_names:
        builtin_assign = js.var(
            builtin_name,
            js.property_access(js.ref("$nope.builtins"), builtin_name),
        )
        js.dump(builtin_assign, fileobj)


def _path_depth(path):
    depth = -1
    while path:
        path, tail = os.path.split(path)
        depth += 1
    
    return depth
        

_main_require = """
(function() {
    // This assumes that executable modules are never imported as ordinary modules
    global.$nopeRequire = function(name) {
        if (isAbsoluteImport(name)) {
            var relativeImportName = "./" + name;
            (function() {
                var fs = require("fs");
                var path = require("path");
            })();
            if (isValidModulePath(relativeImportName)) {
                return require(relativeImportName);
            }
        }
    };

    function isAbsoluteImport(name) {
        return name.indexOf(".") !== 0;
    }

    function isValidModulePath(name) {
        try {
            require.resolve(name);
            return true;
        } catch(error) {
            return false;
        }
    }
})();
"""

_define_require = """
function $require(module) {
    if (global.$nopeRequire) {
        var result = global.$nopeRequire(module);
        if (result) {
            return result;
        }
    }
    return require(module);
}
"""
