import io
import functools
import json

import dodge

from .. import oo
from ..oo import (
    PropertyAccess, property_access,
    BinaryOperation, binary_operation,
    UnaryOperation, unary_operation,
    Call, call,
    VariableReference, ref,
    Number, number, 
    NullLiteral, null,
    Boolean, boolean,
    String, string)


def dump(obj, fileobj, **kwargs):
    writer = _Writer(fileobj, **kwargs)
    writer.dump(obj)


def dumps(obj, **kwargs):
    output = io.StringIO()
    dump(obj, output, **kwargs)
    return output.getvalue()


class _Writer(object):
    def __init__(self, writer, **kwargs):
        self._writer = writer
        self._pretty_print = kwargs.pop("pretty_print", True)
        self._indentation = 0
        self._pending_indentation = False
        assert not kwargs
    
    def write(self, value):
        if self._pending_indentation:
            self._writer.write(" " * (self._indentation * 4))
            self._pending_indentation = False
        
        self._writer.write(value)
    
    def dump(self, node):
        _serializers[type(node)](node, self)
    
    def newline(self):
        if self._pretty_print:
            self.write("\n")
            self._pending_indentation = True
    
    def start_block(self):
        if self._pretty_print:
            self.write("{")
            self._indentation += 1
            self.newline()
        else:
            self.write("{ ")
    
    def end_block(self):
        if self._pretty_print:
            self._indentation -= 1
            self.write("}")
            self.newline()
        else:
            self.write(" }")


def _serialize_statements(obj, writer):
    for statement in obj.statements:
        writer.dump(statement)


def _simple_statement(func):
    @functools.wraps(func)
    def write(value, writer):
        func(value, writer)
        writer.write(";")
        writer.newline()
    
    return write
    


@_simple_statement
def _serialize_expression_statement(obj, writer):
    writer.dump(obj.value)


def _serialize_function_declaration(obj, writer):
    _serialize_function(obj, writer, name=obj.name)


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
    _serialize_block(obj.body, writer)


@_simple_statement
def _serialize_return_statement(obj, writer):
    writer.write("return ")
    writer.dump(obj.value)


@_simple_statement
def _serialize_variable_declaration(obj, writer):
    writer.write("var ")
    writer.write(obj.name)
    
    if obj.value is not None:
        writer.write(" = ")
        writer.dump(obj.value)


def _serialize_if_else(obj, writer):
    writer.write("if (")
    writer.dump(obj.condition)
    writer.write(") ")
    _serialize_block(obj.true_body, writer)
    if obj.false_body:
        writer.write(" else ")
        _serialize_block(obj.false_body, writer)


def _serialize_while_loop(obj, writer):
    writer.write("while (")
    writer.dump(obj.condition)
    writer.write(") ")
    _serialize_block(obj.body, writer)


@_simple_statement
def _serialize_break_statement(obj, writer):
    writer.write("break")


@_simple_statement
def _serialize_continue_statement(obj, writer):
    writer.write("continue")


def _serialize_try_catch(obj, writer):
    writer.write("try ")
    _serialize_block(obj.try_body, writer)
    
    if obj.catch_body:
        writer.write(" catch (")
        writer.write(obj.error_name)
        writer.write(") ")
        _serialize_block(obj.catch_body, writer)
    
    if obj.finally_body:
        writer.write(" finally ")
        _serialize_block(obj.finally_body, writer)


def _serialize_block(statements, writer):
    writer.start_block()
    for statement in statements:
        writer.dump(statement)
    writer.end_block()


@_simple_statement
def _serialize_throw(obj, writer):
    writer.write("throw ")
    writer.dump(obj.value)


def _serialize_assignment(obj, writer):
    writer.dump(obj.target)
    writer.write(" = ")
    writer.dump(obj.value)


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

statements = Statements = dodge.data_class("Statements", ["statements"])

expression_statement = ExpressionStatement = dodge.data_class("ExpressionStatement", ["value"])
function_declaration = FunctionDeclaration = dodge.data_class("FunctionDeclaration", ["name", "args", "body"])
function_expression = FunctionExpression = dodge.data_class("FunctionExpression", ["args", "body"])
ret = ReturnStatement = dodge.data_class("ReturnStatement", ["value"])

VariableDeclaration = dodge.data_class("VariableDeclaration", ["name", "value"])

def var(name, value=None):
    return VariableDeclaration(name, value)

if_else = IfElse = dodge.data_class("IfElse", ["condition", "true_body", "false_body"])
TryCatch = dodge.data_class("TryCatch", ["try_body", "error_name", "catch_body", "finally_body"])

def try_catch(try_body, error_name=None, catch_body=None, finally_body=None):
    return TryCatch(try_body, error_name, catch_body, finally_body)
    

while_loop = WhileLoop = dodge.data_class("WhileLoop", ["condition", "body"])
break_statement = BreakStatement = dodge.data_class("BreakStatement", [])
continue_statement = ContinueStatement = dodge.data_class("ContinueStatement", [])
throw = Throw = dodge.data_class("Throw", ["value"])

Assignment = dodge.data_class("Assignment", ["target", "value"])

def assign(target, value):
    if isinstance(target, str):
        target = ref(target)
    
    return Assignment(target, value)

def assign_statement(target, value):
    return expression_statement(assign(target, value))


array = Array = dodge.data_class("Array", ["elements"])
obj = Object = dodge.data_class("Object", ["properties"])

_serializers = oo.serializers({
    Statements: _serialize_statements,
    
    ExpressionStatement: _serialize_expression_statement,
    FunctionDeclaration: _serialize_function_declaration,
    FunctionExpression: _serialize_function_expression,
    ReturnStatement: _serialize_return_statement,
    VariableDeclaration: _serialize_variable_declaration,
    IfElse: _serialize_if_else,
    WhileLoop: _serialize_while_loop,
    BreakStatement: _serialize_break_statement,
    ContinueStatement: _serialize_continue_statement,
    TryCatch: _serialize_try_catch,
    Throw: _serialize_throw,
    
    Assignment: _serialize_assignment,
    Array: _serialize_array,
    Object: _serialize_object,
})
