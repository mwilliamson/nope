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


internal class __NopeBoolean
{
    internal static readonly __NopeBoolean True = new __NopeBoolean(true);
    internal static readonly __NopeBoolean False = new __NopeBoolean(false);
    
    internal static __NopeBoolean Value(bool value)
    {
        return value ? True : False;
    }
    
    private readonly bool _value;
    
    private __NopeBoolean(bool value)
    {
        _value = value;
    }
    
    internal bool __Value { get { return _value; } }
    internal __NopeBoolean __Negate()
    {
        return _value ? False : True;
    }
    
    public __NopeBoolean __bool__()
    {
        return this;
    }
    
    public override string ToString()
    {
        return _value ? "True" : "False";
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
    
    public __NopeInteger __sub__(__NopeInteger other)
    {
        return Value(_value - other._value);
    }
    
    public __NopeInteger __mul__(__NopeInteger other)
    {
        return Value(_value * other._value);
    }
    
    public __NopeFloat __truediv__(__NopeInteger other)
    {
        return __NopeFloat.Value((double)_value / (double)other._value);
    }
    
    public __NopeInteger __floordiv__(__NopeInteger other)
    {
        return __NopeInteger.Value(__floordiv__int(_value, other._value));
    }
    
    private static int __floordiv__int(int left, int right)
    {
        var roundedTowardsZero = left / right;
        var wasRounded = (left % right) != 0;
        
        if (wasRounded && (left < 0 ^ right < 0)) {
            return roundedTowardsZero - 1;
        }
        else
        {
            return roundedTowardsZero;
        }
    }
    
    public __NopeInteger __mod__(__NopeInteger other)
    {
        return Value((_value % other._value + other._value) % other._value);
    }
    
    public __NopeTuple __divmod__(__NopeInteger other)
    {
        return __NopeTuple.Values(
            __floordiv__(other),
            __mod__(other)
        );
    }
    
    public __NopeFloat __pow__(__NopeInteger other)
    {
        return __NopeFloat.Value(System.Math.Pow(_value, other._value));
    }
    
    public __NopeInteger __pos__()
    {
        return this;
    }
    
    public __NopeInteger __neg__()
    {
        return Value(-_value);
    }
    
    public __NopeInteger __abs__()
    {
        return Value(System.Math.Abs(_value));
    }
    
    public __NopeInteger __invert__()
    {
        return Value(~_value);
    }
    
    public __NopeInteger __lshift__(__NopeInteger other)
    {
        return Value(_value << other._value);
    }
    
    public __NopeInteger __rshift__(__NopeInteger other)
    {
        return Value(_value >> other._value);
    }
    
    public __NopeInteger __and__(__NopeInteger other)
    {
        return Value(_value & other._value);
    }
    
    public __NopeInteger __or__(__NopeInteger other)
    {
        return Value(_value | other._value);
    }
    
    public __NopeInteger __xor__(__NopeInteger other)
    {
        return Value(_value ^ other._value);
    }
    
    public override string ToString()
    {
        return _value.ToString();
    }
}


internal class __NopeFloat
{
    internal static __NopeFloat Value(double value)
    {
        return new __NopeFloat(value);
    }
    
    private readonly double _value;
    
    private __NopeFloat(double value)
    {
        _value = value;
    }
    
    public override string ToString()
    {
        return _value.ToString();
    }
}


internal class __NopeTuple
{
    internal static __NopeTuple Values(params dynamic[] values)
    {
        return new __NopeTuple(values);
    }
    
    private readonly dynamic[] _values;
    
    private __NopeTuple(dynamic[] values)
    {
        _values = values;
    }
    
    public override string ToString()
    {
        return "(" + string.Join(", ", System.Linq.Enumerable.Select(_values, value => value.ToString())) + ")";
    }
}

internal class __NopeList
{
    internal static __NopeList Values(params dynamic[] values)
    {
        return new __NopeList(values);
    }
    
    private readonly dynamic[] _values;
    
    private __NopeList(dynamic[] values)
    {
        _values = values;
    }
    
    public override string ToString()
    {
        return "[" + string.Join(", ", System.Linq.Enumerable.Select(_values, value => value.ToString())) + "]";
    }
}

namespace __Nope
{
    internal class Builtins
    {
        internal static __NopeBoolean @bool(dynamic value)
        {
            if (value.GetType().GetMethod("__bool__") != null)
            {
                return value.__bool__();
            }
            else
            {
                return __NopeBoolean.False;
            }
        }
    }
    
    internal class Internals
    {
        internal static __NopeBoolean op_is(object left, object right)
        {
            return __NopeBoolean.Value(System.Object.ReferenceEquals(left, right));
        }
        
        internal static __NopeBoolean op_is_not(object left, object right)
        {
            return __NopeBoolean.Value(!System.Object.ReferenceEquals(left, right));
        }
    }
}


internal class Program
{
    internal static void Main()
    {
        System.Func<dynamic, dynamic> abs = x => x.__abs__();
        System.Func<dynamic, dynamic, dynamic> divmod = (x, y) => x.__divmod__(y);
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


def _transform_all(nodes):
    return list(map(_transform, nodes))


def _transform_module(module):
    return cs.statements(_transform_all(module.body))


def _transform_function_definition(function):
    func_type = cs.type_apply(cs.ref("System.Func"), [cs.dynamic] * (len(function.args) + 1))
    args = [cs.arg(arg.name) for arg in function.args]
    body = _transform_all(function.body)
    lambda_expression = cs.lambda_(args, body)
    assignment = cs.assign(cs.ref(function.name), cs.cast(func_type, lambda_expression))
    return cs.expression_statement(assignment)


def _transform_if_statement(statement):
    return cs.if_(
        cs.property_access(_transform(statement.condition), "__Value"),
        _transform_all(statement.true_body),
        _transform_all(statement.false_body)
    )


def _transform_expression_statement(statement):
    return cs.expression_statement(_transform(statement.value))


def _transform_variable_declaration(declaration):
    return cs.declare(declaration.name)


def _transform_binary_operation(operation):
    if operation.operator in ["is", "is_not"]:
        return _transform_is(operation)
    else:
        raise Exception("Unhandled operator: {}".format(operation.operator))


def _transform_is(operation):
    return cs.call(cs.ref("__Nope.Internals.op_{}".format(operation.operator)), [
        _transform(operation.left),
        _transform(operation.right),
    ])


def _transform_return_statement(statement):
    return cs.ret(_transform(statement.value))


def _transform_assignment(assignment):
    return cs.expression_statement(cs.assign(_transform(assignment.target), _transform(assignment.value)))


def _transform_list_literal(literal):
    return cs.call(cs.ref("__NopeList.Values"), _transform_all(literal.elements))


def _transform_call(call):
    return cs.call(_transform(call.func), _transform_all(call.args))


def _transform_attribute_access(node):
    return cs.property_access(_transform(node.obj), node.attr)


def _transform_builtin_reference(reference):
    return cs.ref("__Nope.Builtins.@{}".format(reference.name))


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
    
    cc.IfStatement: _transform_if_statement,
    
    cc.ExpressionStatement: _transform_expression_statement,
    cc.VariableDeclaration: _transform_variable_declaration,
    cc.ReturnStatement: _transform_return_statement,
    
    cc.Assignment: _transform_assignment,
    cc.ListLiteral: _transform_list_literal,
    cc.BinaryOperation: _transform_binary_operation,
    cc.Call: _transform_call,
    cc.AttributeAccess: _transform_attribute_access,
    cc.BuiltinReference: _transform_builtin_reference,
    cc.VariableReference: _transform_variable_reference,
    cc.StrLiteral: _transform_string_literal,
    cc.IntLiteral: _transform_int_literal,
    cc.NoneLiteral: _transform_none_literal,
}
