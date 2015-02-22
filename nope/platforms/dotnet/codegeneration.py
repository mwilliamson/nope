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
        System.Func<dynamic, dynamic> abs = __x_1 => __x_1.__abs__();
        System.Func<dynamic, dynamic, dynamic> divmod = (__x_1, __y_1) => __x_1.__divmod__(__y_1);
        System.Func<dynamic, dynamic, dynamic> range = (__x_1, __y_1) => __Nope.Builtins.range(__x_1, __y_1);
        System.Action<object> print = System.Console.WriteLine;
        var Exception = __Nope.Builtins.Exception;
        var AssertionError = __Nope.Builtins.AssertionError;
        var str = __Nope.Builtins.str;
        """)
        
                cs.dump(cs_module, dest_cs_file)
                dest_cs_file.write("""
    }
}
""")
            subprocess.check_call(["mcs", "-out:{}".format(dest_exe_filename), dest_cs_filename] + list(_runtime_paths()))
        
        walk_tree(source_path, handle_dir, handle_file)


def _runtime_paths():
    path = os.path.join(os.path.dirname(__file__), "runtime")
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(root, filename)

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


def _transform_try_statement(statement):
    if statement.handlers:
        catch = [_transform_except_handlers(statement.handlers)]
    else:
        catch = []
    
    return cs.try_(
        _transform_all(statement.body),
        catch,
        finally_body=_transform_all(statement.finally_body),
    )


def _transform_except_handlers(handlers):
    catch_body = [cs.throw()]
    
    dotnet_exception_name = "__exception"
    dotnet_exception = cs.ref(dotnet_exception_name)
    
    nope_exception = cs.property_access(dotnet_exception, "__Value")
    
    for handler in reversed(handlers):
        handler_body = _transform_all(handler.body)
        
        if handler.type is None:
            catch_body = handler_body
        else:
            if handler.target is None:
                before_body = []
            else:
                before_body = [cs.expression_statement(cs.assign(cs.ref(handler.target.name), nope_exception))]
            
            catch_body = [
                cs.if_(
                    cs.property_access(cs.call(_builtin_ref("isinstance"), [nope_exception, _transform(handler.type)]), "__Value"),
                    before_body + handler_body,
                    catch_body,
                )
            ]
    
    return cs.catch(_internal_ref("__NopeException"), dotnet_exception_name, catch_body)


def _transform_raise_statement(statement):
    return cs.throw(cs.call(_internal_ref("CreateException"), [_transform(statement.value)]))


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
    return _builtin_ref(reference.name)


def _builtin_ref(name):
    return cs.ref("__Nope.Builtins.@{}".format(name))


def _transform_internal_reference(reference):
    return _internal_ref(reference.name)


def _internal_ref(name):
    return cs.ref("__Nope.Internals.@{}".format(name))


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
    
    cc.TryStatement: _transform_try_statement,
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
