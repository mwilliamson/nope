import os
import subprocess

import zuice

from ... import files
from ...walk import walk_tree
from ...injection import CouscousTree
from . import cs
from ... import couscous as cc


class CodeGenerator(zuice.Base):
    _source_tree = zuice.dependency(CouscousTree)
    
    def generate_files(self, source_path, destination_root):
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_root, relative_path))
        
        def handle_file(path, relative_path):
            module = self._source_tree.module(path)
            dest_cs_filename = files.replace_extension(
                os.path.join(destination_root, relative_path),
                "cs"
            )
            dest_exe_filename = files.replace_extension(dest_cs_filename, "exe")
            
            with open(dest_cs_filename, "w") as dest_cs_file:
                cs_module = _transform(module.node)
                
                dest_cs_file.write("""
internal class Program
{
    internal static void Main()
    {
        System.Action<object> print = System.Console.WriteLine;""")
        
                cs.dump(cs_module, dest_cs_file)
        
                dest_cs_file.write("""
    }
}
""")
            subprocess.check_call(["mcs", dest_cs_filename, "-out:{}".format(dest_exe_filename)])
        
        walk_tree(source_path, handle_dir, handle_file)


def _transform(node):
    return _transformers[type(node)](node)


def _transform_module(module):
    return cs.statements(list(map(_transform, module.body)))


def _transform_expression_statement(statement):
    return cs.expression_statement(_transform(statement.value))


def _transform_call(call):
    return cs.call(_transform(call.func), list(map(_transform, call.args)))


def _transform_variable_reference(reference):
    return cs.ref(reference.name)


def _transform_int_literal(literal):
    return cs.integer_literal(literal.value)


_transformers = {
    cc.Module: _transform_module,
    
    cc.ExpressionStatement: _transform_expression_statement,
    
    cc.Call: _transform_call,
    cc.VariableReference: _transform_variable_reference,
    cc.IntLiteral: _transform_int_literal,
}
