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
internal class __NopeNone
{
    internal static readonly __NopeNone Value = new __NopeNone();
    private __NopeNone() { }
    
    public override string ToString()
    {
        return "None";
    }
}


internal class __NopeInteger
{
    internal static __NopeInteger Value(int value)
    {
        return new __NopeInteger(value);
    }
    
    private readonly int _value;
    
    private __NopeInteger(int value)
    {
        _value = value;
    }
    
    public __NopeInteger __add__(__NopeInteger other)
    {
        return Value(_value + other._value);
    }
    
    public override string ToString()
    {
        return _value.ToString();
    }
}


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


def _transform_function_definition(function):
    func_type = cs.type_apply(cs.ref("System.Func"), [cs.dynamic] * (len(function.args) + 1))
    args = [cs.arg(arg.name) for arg in function.args]
    body = list(map(_transform, function.body))
    lambda_expression = cs.lambda_(args, body)
    assignment = cs.assign(cs.ref(function.name), cs.cast(func_type, lambda_expression))
    return cs.expression_statement(assignment)


def _transform_expression_statement(statement):
    return cs.expression_statement(_transform(statement.value))


def _transform_variable_declaration(declaration):
    return cs.declare(declaration.name)


def _transform_return_statement(statement):
    return cs.ret(_transform(statement.value))


def _transform_call(call):
    return cs.call(_transform(call.func), list(map(_transform, call.args)))


def _transform_attribute_access(node):
    return cs.property_access(_transform(node.obj), node.attr)


def _transform_variable_reference(reference):
    return cs.ref(reference.name)


def _transform_string_literal(literal):
    return cs.string_literal(literal.value)


def _transform_int_literal(literal):
    return cs.call(cs.ref("__NopeInteger.Value"), [cs.integer_literal(literal.value)])


def _transform_none_literal(literal):
    return cs.ref("__NopeNone.Value")


_transformers = {
    cc.Module: _transform_module,
    
    cc.FunctionDefinition: _transform_function_definition,
    
    cc.ExpressionStatement: _transform_expression_statement,
    cc.VariableDeclaration: _transform_variable_declaration,
    cc.ReturnStatement: _transform_return_statement,
    
    cc.Call: _transform_call,
    cc.AttributeAccess: _transform_attribute_access,
    cc.VariableReference: _transform_variable_reference,
    cc.StrLiteral: _transform_string_literal,
    cc.IntLiteral: _transform_int_literal,
    cc.NoneLiteral: _transform_none_literal,
}
