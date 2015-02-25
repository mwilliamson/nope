import io
import functools
import json

import dodge

from .. import oo
from ..oo import (
    Writer,
    
    Statements, statements,
    
    IfElse, if_,
    WhileLoop, while_,
    ContinueStatement, continue_,
    BreakStatement, break_,
    
    Throw, throw,
    
    ExpressionStatement, expression_statement,
    ReturnStatement, ret,
    
    assignment_expression as assign,
    PropertyAccess, property_access,
    BinaryOperation, binary_operation,
    UnaryOperation, unary_operation,
    TernaryConditional, ternary_conditional,
    Call, call,
    VariableReference, ref,
    Number, number, 
    NullLiteral, null,
    Boolean, boolean,
    String, string)


def dump(obj, fileobj, **kwargs):
    writer = Writer(_serializers, fileobj, **kwargs)
    writer.dump(obj)


def dumps(obj, **kwargs):
    output = io.StringIO()
    dump(obj, output, **kwargs)
    return output.getvalue()


def _serialize_function_declaration(obj, writer):
    _serialize_function(obj, writer, name=obj.name)
    writer.end_compound_statement()


def _serialize_function_expression(obj, writer):
    _serialize_function(obj, writer, name=None)


def _serialize_function(obj, writer, name):
    writer.write("function")
    if name is not None:
        writer.write(" ")
        writer.write(name)
    writer.write("(")
    
    for index, arg in enumerate(obj.args):
        if index > 0:
            writer.write(", ")
        writer.write(arg)
    
    writer.write(") ")
    writer.dump_block(obj.body)


def _serialize_variable_declaration(obj, writer):
    writer.write("var ")
    writer.write(obj.name)
    
    if obj.value is not None:
        writer.write(" = ")
        writer.dump(obj.value)
    
    writer.end_simple_statement()


def _serialize_try_catch(obj, writer):
    writer.write("try ")
    writer.dump_block(obj.try_body)
    
    if obj.catch_body:
        writer.write(" catch (")
        writer.write(obj.error_name)
        writer.write(") ")
        writer.dump_block(obj.catch_body)
    
    if obj.finally_body:
        writer.write(" finally ")
        writer.dump_block(obj.finally_body)
    
    writer.end_compound_statement()


def _serialize_array(obj, writer):
    writer.write("[")
    
    for index, arg in enumerate(obj.elements):
        if index > 0:
            writer.write(", ")
        writer.dump(arg)
    
    writer.write("]")

def _serialize_object(obj, writer):
    writer.write("{")
    
    for index, (key, value) in enumerate(obj.properties.items()):
        if index > 0:
            writer.write(", ")
            
        json.dump(key, writer)
        writer.write(": ")
        writer.dump(value)
        
    writer.write("}")

function_declaration = FunctionDeclaration = dodge.data_class("FunctionDeclaration", ["name", "args", "body"])
function_expression = FunctionExpression = dodge.data_class("FunctionExpression", ["args", "body"])

VariableDeclaration = dodge.data_class("VariableDeclaration", ["name", "value"])

def var(name, value=None):
    return VariableDeclaration(name, value)

TryCatch = dodge.data_class("TryCatch", ["try_body", "error_name", "catch_body", "finally_body"])

def try_(try_body, error_name=None, catch_body=None, finally_body=None):
    return TryCatch(try_body, error_name, catch_body, finally_body)

def assign_statement(target, value):
    return expression_statement(assign(target, value))


array = Array = dodge.data_class("Array", ["elements"])
obj = Object = dodge.data_class("Object", ["properties"])

or_ = functools.partial(binary_operation, "||")
and_ = functools.partial(binary_operation, "&&")


_serializers = oo.serializers({
    FunctionDeclaration: _serialize_function_declaration,
    FunctionExpression: _serialize_function_expression,
    VariableDeclaration: _serialize_variable_declaration,
    TryCatch: _serialize_try_catch,
    
    Array: _serialize_array,
    Object: _serialize_object,
})
