import io
import json
import functools

import dodge


def dump(obj, fileobj, **kwargs):
    writer = _Writer(fileobj, **kwargs)
    writer.dump(obj)


def dumps(obj, **kwargs):
    output = io.StringIO()
    dump(obj, output, **kwargs)
    return output.getvalue()


class _Writer(object):
    def __init__(self, writer, pretty_print=None):
        self._writer = writer
        self._pretty_print = pretty_print
    
    def write(self, value):
        self._writer.write(value)
    
    def dump(self, node):
        _serializers[type(node)](node, self)
    
    def newline(self):
        if self._pretty_print:
            self._writer.write("\n")


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
    
    writer.write(") { ")
    
    for statement in obj.body:
        writer.dump(statement)
    
    writer.write(" }")


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
    writer.write("{ ")
    for statement in statements:
        writer.dump(statement)
    writer.write(" }")


@_simple_statement
def _serialize_throw(obj, writer):
    writer.write("throw ")
    writer.dump(obj.value)


def _serialize_assignment(obj, writer):
    writer.dump(obj.target)
    writer.write(" = ")
    writer.dump(obj.value)


def _serialize_property_access(obj, writer):
    writer.write("(")
    writer.dump(obj.value)
    writer.write(")")
    if isinstance(obj.property, str):
        writer.write(".")
        writer.write(obj.property)
    else:
        writer.write("[")
        writer.dump(obj.property)
        writer.write("]")


def _serialize_binary_operation(obj, writer):
    writer.write("(")
    writer.dump(obj.left)
    writer.write(") ")
    writer.write(obj.operator)
    writer.write(" (")
    writer.dump(obj.right)
    writer.write(")")


def _serialize_unary_operation(obj, writer):
    writer.write(obj.operator)
    writer.write("(")
    writer.dump(obj.operand)
    writer.write(")")


def _serialize_call(obj, writer):
    writer.dump(obj.func)
    writer.write("(")
    
    for index, arg in enumerate(obj.args):
        if index > 0:
            writer.write(", ")
        writer.dump(arg)
    
    writer.write(")")
    

def _serialize_ref(obj, writer):
    writer.write(obj.name)


def _serialize_number(obj, writer):
    writer.write(str(obj.value))


def _serialize_null(obj, writer):
    writer.write("null")


def _serialize_boolean(obj, writer):
    serialized_value = "true" if obj.value else "false"
    writer.write(serialized_value)


def _serialize_string(obj, writer):
    json.dump(obj.value, writer)


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

property_access = PropertyAccess = dodge.data_class("PropertyAccess", ["value", "property"])
binary_operation = BinaryOperation = dodge.data_class("BinaryOperation", ["operator", "left", "right"])
unary_operation = UnaryOperation = dodge.data_class("UnaryOperation", ["operator", "operand"])
call = Call = dodge.data_class("Call", ["func", "args"])
ref = VariableReference = dodge.data_class("VariableReference", ["name"])
number = Number = dodge.data_class("Number", ["value"])
NullLiteral = dodge.data_class("NullLiteral", [])
null = NullLiteral()
boolean = Boolean = dodge.data_class("Boolean", ["value"])
string = String = dodge.data_class("String", ["value"])
array = Array = dodge.data_class("Array", ["elements"])
obj = Object = dodge.data_class("Object", ["properties"])

_serializers = {
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
    PropertyAccess: _serialize_property_access,
    BinaryOperation: _serialize_binary_operation,
    UnaryOperation: _serialize_unary_operation,
    Call: _serialize_call,
    VariableReference: _serialize_ref,
    Number: _serialize_number,
    NullLiteral: _serialize_null,
    Boolean: _serialize_boolean,
    String: _serialize_string,
    Array: _serialize_array,
    Object: _serialize_object,
}
