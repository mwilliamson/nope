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
    
    internal int __Value { get { return _value; } }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_value != 0);
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
    
    public __NopeBoolean __eq__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value == other._value);
    }
    
    public __NopeBoolean __ne__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value != other._value);
    }
    
    public __NopeBoolean __le__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value <= other._value);
    }
    
    public __NopeBoolean __lt__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value < other._value);
    }
    
    public __NopeBoolean __ge__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value >= other._value);
    }
    
    public __NopeBoolean __gt__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value > other._value);
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
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_value != 0);
    }
    
    public override string ToString()
    {
        return _value.ToString();
    }
}


internal class __NopeString
{
    internal static __NopeString Value(string value)
    {
        return new __NopeString(value);
    }
    
    private readonly string _value;
    
    private __NopeString(string value)
    {
        _value = value;
    }
    
    internal string __Value { get { return _value; } }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_value.Length > 0);
    }
    
    public override string ToString()
    {
        return _value;
    }
    
    public int find(__NopeString substring)
    {
        return _value.IndexOf(substring._value);
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
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_values.Length > 0);
    }
    
    public dynamic __getitem__(__NopeInteger key)
    {
        var index = key.__Value;
        return index < 0 ? _values[_values.Length + index] : _values[index];
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
        return new __NopeList(new System.Collections.Generic.List<dynamic>(values));
    }
    
    private readonly System.Collections.Generic.IList<dynamic> _values;
    
    internal __NopeList() : this(new System.Collections.Generic.List<dynamic>())
    {
    }
    
    private __NopeList(System.Collections.Generic.IList<dynamic> values)
    {
        _values = values;
    }
    
    internal Iterator __iter__()
    {
        return new Iterator(_values);
    }
    
    internal class Iterator
    {
        private readonly System.Collections.Generic.IList<dynamic> _values;
        private int _nextIndex = 0;
    
        internal Iterator(System.Collections.Generic.IList<dynamic> values)
        {
            _values = values;
        }
        
        internal dynamic __next__()
        {
            if (_nextIndex < _values.Count)
            {
                return _values[_nextIndex++];
            }
            else
            {
                throw new __Nope.Builtins.StopIteration();
            }
        }
    }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_values.Count > 0);
    }
    
    public dynamic __getitem__(dynamic key)
    {
        if (key is __Nope.Builtins.Slice)
        {
            // TODO: exception on step of 0
            // TODO: implement this in nope
            var result = new __NopeList();
            var step = System.Object.ReferenceEquals(key.step, __NopeNone.Value)
                ? 1 : key.step.__Value;
            
            if (step < 0)
            {
                var start = System.Object.ReferenceEquals(key.start, __NopeNone.Value)
                    ? _values.Count - 1
                    : key.start.__Value;
                var stop = System.Object.ReferenceEquals(key.stop, __NopeNone.Value)
                    ? -1 : key.stop.__Value;
                
                for (var i = start; i > stop; i += step) {
                    result.append(_values[i]);
                }
            }
            else
            {
                var start = System.Object.ReferenceEquals(key.start, __NopeNone.Value)
                    ? 0 : key.start.__Value;
                var stop = System.Object.ReferenceEquals(key.stop, __NopeNone.Value)
                    ? _values.Count : key.stop.__Value;
                
                for (var i = start; i < stop; i += step) {
                    result.append(_values[i]);
                }
            }
            return result;
        }
        else
        {
            var index = key.__Value;
            return index < 0 ? _values[_values.Count + index] : _values[index];
        }
    }
    
    public void __setitem__(__NopeInteger key, dynamic value)
    {
        _values[key.__Value] = value;
    }
    
    public void append(dynamic value)
    {
        _values.Add(value);
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
        // TODO: resolve needing AssertionError to be both a class and a callable
        internal class _AssertionError : System.Exception
        {
            internal _AssertionError(__NopeString message) : base(message.__Value)
            {
            }
        }
    
        internal static _AssertionError AssertionError(__NopeString message)
        {
            return new _AssertionError(message);
        }
    
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
        
        internal static dynamic next(dynamic iterator, dynamic stopValue)
        {
            try
            {
                return iterator.__next__();
            }
            catch (StopIteration)
            {
                return stopValue;
            }
        }
        
        internal static dynamic iter(dynamic iterable)
        {
            return iterable.__iter__();
        }
        
        internal class StopIteration : System.Exception
        {
        }
        
        internal static RangeIterator range(__NopeInteger start, __NopeInteger end)
        {
            return new RangeIterator(start.__Value, end.__Value);
        }
        
        internal class RangeIterator
        {
            private int _index;
            private readonly int _end;
        
            internal RangeIterator(int start, int end)
            {
                _index = start;
                _end = end;
            }
            
            internal RangeIterator __iter__()
            {
                return this;
            }
            
            internal __NopeInteger __next__()
            {
                if (_index < _end)
                {
                    return __NopeInteger.Value(_index++);
                }
                else
                {
                    throw new StopIteration();
                }
            }
        }
        
        internal static Slice slice(dynamic start, dynamic stop, dynamic step)
        {
            return new Slice(start, stop, step);
        }
        
        internal class Slice
        {
            private readonly dynamic _start;
            private readonly dynamic _stop;
            private readonly dynamic _step;
            
            internal Slice(dynamic start, dynamic stop, dynamic step)
            {
                _start = start;
                _stop = stop;
                _step = step;
            }
            
            internal dynamic start { get { return _start; } }
            internal dynamic stop { get { return _stop; } }
            internal dynamic step { get { return _step; } }
        }
    }
    
    internal class Internals
    {
        internal static readonly object loop_sentinel = new object();
    
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
        System.Func<dynamic, dynamic> abs = __x_1 => __x_1.__abs__();
        System.Func<dynamic, dynamic, dynamic> divmod = (__x_1, __y_1) => __x_1.__divmod__(__y_1);
        System.Func<dynamic, dynamic, dynamic> range = (__x_1, __y_1) => __Nope.Builtins.range(__x_1, __y_1);
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


def _transform_or_none(node):
    if node is None:
        return None
    else:
        return _transform(node)


def _transform_module(module):
    return cs.statements(_transform_all(module.body))


def _transform_statements(node):
    return cs.statements(_transform_all(node.body))


def _transform_function_definition(function):
    func_type = cs.type_apply(cs.ref("System.Func"), [cs.dynamic] * (len(function.args) + 1))
    args = [cs.arg(arg.name) for arg in function.args]
    body = _transform_all(function.body)
    lambda_expression = cs.lambda_(args, body)
    assignment = cs.assign(cs.ref(function.name), cs.cast(func_type, lambda_expression))
    return cs.expression_statement(assignment)


def _transform_if_statement(statement):
    return cs.if_(
        _transform_condition(statement.condition),
        _transform_all(statement.true_body),
        _transform_all(statement.false_body)
    )


def _transform_while_loop(statement):
    return cs.while_(
        _transform_condition(statement.condition),
        _transform_all(statement.body),
    )

def _transform_condition(condition):
    return cs.property_access(_transform(condition), "__Value")


def _transform_raise_statement(statement):
    return cs.throw(_transform(statement.value))


def _transform_expression_statement(statement):
    return cs.expression_statement(_transform(statement.value))


def _transform_variable_declaration(declaration):
    if declaration.value is None:
        value = cs.null
    else:
        value = _transform(declaration.value)
    return cs.declare(declaration.name, value)


def _transform_operation(operation):
    if operation.operator in ["is", "is_not"]:
        return _transform_is(operation)
    elif operation.operator == "not":
        return _transform_not(operation)
    else:
        raise Exception("Unhandled operator: {}".format(operation.operator))


def _transform_ternary_conditional(conditional):
    return cs.ternary_conditional(
        _transform_condition(conditional.condition),
        _transform(conditional.true_value),
        _transform(conditional.false_value),
    )


def _transform_is(operation):
    return cs.call(cs.ref("__Nope.Internals.op_{}".format(operation.operator)), [
        _transform(operation.left),
        _transform(operation.right),
    ])


def _transform_not(operation):
    return cs.call(cs.property_access(_transform(operation.operand), "__Negate"), [])


def _transform_return_statement(statement):
    return cs.ret(_transform(statement.value))


def _transform_assignment(assignment):
    return cs.expression_statement(cs.assign(_transform(assignment.target), _transform(assignment.value)))


def _transform_list_literal(literal):
    return cs.call(cs.ref("__NopeList.Values"), _transform_all(literal.elements))


def _transform_tuple_literal(literal):
    return cs.call(cs.ref("__NopeTuple.Values"), _transform_all(literal.elements))


def _transform_call(call):
    return cs.call(_transform(call.func), _transform_all(call.args))


def _transform_attribute_access(node):
    return cs.property_access(_transform(node.obj), node.attr)


def _transform_builtin_reference(reference):
    return cs.ref("__Nope.Builtins.@{}".format(reference.name))


def _transform_internal_reference(reference):
    return cs.ref("__Nope.Internals.@{}".format(reference.name))


def _transform_variable_reference(reference):
    return cs.ref(reference.name)


def _transform_string_literal(literal):
    return cs.call(cs.ref("__NopeString.Value"), [cs.string_literal(literal.value)])


def _transform_int_literal(literal):
    return cs.call(cs.ref("__NopeInteger.Value"), [cs.integer_literal(literal.value)])


def _transform_bool_literal(literal):
    return cs.ref("__NopeBoolean.{}".format("True" if literal.value else "False"))


def _transform_none_literal(literal):
    return cs.ref("__NopeNone.Value")


_transformers = {
    cc.Module: _transform_module,
    
    cc.Statements: _transform_statements,
    
    cc.FunctionDefinition: _transform_function_definition,
    
    cc.IfStatement: _transform_if_statement,
    cc.WhileLoop: _transform_while_loop,
    cc.BreakStatement: lambda node: cs.break_,
    cc.ContinueStatement: lambda node: cs.continue_,
    
    cc.RaiseStatement: _transform_raise_statement,
    
    cc.ExpressionStatement: _transform_expression_statement,
    cc.VariableDeclaration: _transform_variable_declaration,
    cc.ReturnStatement: _transform_return_statement,
    
    cc.Assignment: _transform_assignment,
    cc.ListLiteral: _transform_list_literal,
    cc.TupleLiteral: _transform_tuple_literal,
    cc.BinaryOperation: _transform_operation,
    cc.UnaryOperation: _transform_operation,
    cc.TernaryConditional: _transform_ternary_conditional,
    cc.Call: _transform_call,
    cc.AttributeAccess: _transform_attribute_access,
    cc.BuiltinReference: _transform_builtin_reference,
    cc.InternalReference: _transform_internal_reference,
    cc.VariableReference: _transform_variable_reference,
    cc.StrLiteral: _transform_string_literal,
    cc.IntLiteral: _transform_int_literal,
    cc.BooleanLiteral: _transform_bool_literal,
    cc.NoneLiteral: _transform_none_literal,
}
