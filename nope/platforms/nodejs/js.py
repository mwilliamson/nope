import collections
import io
import json


def dump(obj, fileobj):
    _serializers[type(obj)](obj, fileobj)


def dumps(obj):
    output = io.StringIO()
    dump(obj, output)
    return output.getvalue()


def _serialize_statements(obj, fileobj):
    for statement in obj.statements:
        dump(statement, fileobj)


def _serialize_expression_statement(obj, fileobj):
    dump(obj.value, fileobj)
    fileobj.write(";")


def _serialize_function_declaration(obj, fileobj):
    _serialize_function(obj, fileobj, name=obj.name)


def _serialize_function_expression(obj, fileobj):
    _serialize_function(obj, fileobj, name=None)


def _serialize_function(obj, fileobj, name):
    fileobj.write("function")
    if name is not None:
        fileobj.write(" ")
        fileobj.write(name)
    fileobj.write("(")
    
    for index, arg in enumerate(obj.args):
        if index > 0:
            fileobj.write(", ");
        fileobj.write(arg)
    
    fileobj.write(") { ")
    
    for statement in obj.body:
        dump(statement, fileobj)
    
    fileobj.write(" }")


def _serialize_return_statement(obj, fileobj):
    fileobj.write("return ")
    dump(obj.value, fileobj)
    fileobj.write(";")


def _serialize_variable_declaration(obj, fileobj):
    fileobj.write("var ")
    fileobj.write(obj.name)
    
    if obj.value is not None:
        fileobj.write(" = ")
        dump(obj.value, fileobj)
    
    fileobj.write(";")


def _serialize_if_else(obj, fileobj):
    fileobj.write("if (")
    dump(obj.condition, fileobj)
    fileobj.write(") ");
    _serialize_block(obj.true_body, fileobj)
    fileobj.write(" else ")
    _serialize_block(obj.false_body, fileobj)


def _serialize_while_loop(obj, fileobj):
    fileobj.write("while (")
    dump(obj.condition, fileobj)
    fileobj.write(") ")
    _serialize_block(obj.body, fileobj)


def _serialize_break_statement(obj, fileobj):
    fileobj.write("break;")


def _serialize_continue_statement(obj, fileobj):
    fileobj.write("continue;")


def _serialize_try_catch(obj, fileobj):
    fileobj.write("try ")
    _serialize_block(obj.try_body, fileobj)
    
    if obj.catch_body:
        fileobj.write(" catch (")
        fileobj.write(obj.error_name)
        fileobj.write(") ")
        _serialize_block(obj.catch_body, fileobj)
    
    if obj.finally_body:
        fileobj.write(" finally ")
        _serialize_block(obj.finally_body, fileobj)


def _serialize_block(statements, fileobj):
    fileobj.write("{ ")
    for statement in statements:
        dump(statement, fileobj)
    fileobj.write(" }")


def _serialize_throw(obj, fileobj):
    fileobj.write("throw ");
    dump(obj.value, fileobj)
    fileobj.write(";")


def _serialize_assignment(obj, fileobj):
    dump(obj.target, fileobj)
    fileobj.write(" = ")
    dump(obj.value, fileobj)


def _serialize_property_access(obj, fileobj):
    fileobj.write("(")
    dump(obj.value, fileobj)
    fileobj.write(")")
    if isinstance(obj.property, str):
        fileobj.write(".")
        fileobj.write(obj.property)
    else:
        fileobj.write("[")
        dump(obj.property, fileobj)
        fileobj.write("]")


def _serialize_binary_operation(obj, fileobj):
    fileobj.write("(")
    dump(obj.left, fileobj)
    fileobj.write(") ")
    fileobj.write(obj.operator)
    fileobj.write(" (")
    dump(obj.right, fileobj)
    fileobj.write(")")


def _serialize_unary_operation(obj, fileobj):
    fileobj.write(obj.operator)
    fileobj.write("(")
    dump(obj.operand, fileobj)
    fileobj.write(")")


def _serialize_call(obj, fileobj):
    dump(obj.func, fileobj)
    fileobj.write("(")
    
    for index, arg in enumerate(obj.args):
        if index > 0:
            fileobj.write(", ");
        dump(arg, fileobj)
    
    fileobj.write(")")
    

def _serialize_ref(obj, fileobj):
    fileobj.write(obj.name)


def _serialize_number(obj, fileobj):
    fileobj.write(str(obj.value))


def _serialize_null(obj, fileobj):
    fileobj.write("null")


def _serialize_boolean(obj, fileobj):
    serialized_value = "true" if obj.value else "false"
    fileobj.write(serialized_value)


def _serialize_string(obj, fileobj):
    json.dump(obj.value, fileobj)


def _serialize_array(obj, fileobj):
    fileobj.write("[")
    
    for index, arg in enumerate(obj.elements):
        if index > 0:
            fileobj.write(", ");
        dump(arg, fileobj)
    
    fileobj.write("]")

def _serialize_object(obj, fileobj):
    fileobj.write("{")
    
    for index, (key, value) in enumerate(obj.properties.items()):
        if index > 0:
            fileobj.write(", ");
            
        json.dump(key, fileobj)
        fileobj.write(": ")
        dump(value, fileobj)
        
    fileobj.write("}")

statements = Statements = collections.namedtuple("Statements", ["statements"])

expression_statement = ExpressionStatement = collections.namedtuple("ExpressionStatement", ["value"])
function_declaration = FunctionDeclaration = collections.namedtuple("FunctionDeclaration", ["name", "args", "body"])
function_expression = FunctionExpression = collections.namedtuple("FunctionExpression", ["args", "body"])
ret = ReturnStatement = collections.namedtuple("ReturnStatement", ["value"])

VariableDeclaration = collections.namedtuple("VariableDeclaration", ["name", "value"])

def var(name, value=None):
    return VariableDeclaration(name, value)

if_else = IfElse = collections.namedtuple("IfElse", ["condition", "true_body", "false_body"])
TryCatch = collections.namedtuple("TryCatch", ["try_body", "error_name", "catch_body", "finally_body"])

def try_catch(try_body, error_name=None, catch_body=None, finally_body=None):
    return TryCatch(try_body, error_name, catch_body, finally_body)
    

while_loop = WhileLoop = collections.namedtuple("WhileLoop", ["condition", "body"])
break_statement = BreakStatement = collections.namedtuple("BreakStatement", [])
continue_statement = ContinueStatement = collections.namedtuple("ContinueStatement", [])
throw = Throw = collections.namedtuple("Throw", ["value"])

Assignment = collections.namedtuple("Assignment", ["target", "value"])

def assign(target, value):
    if isinstance(target, str):
        target = ref(target)
    
    return Assignment(target, value)

def assign_statement(target, value):
    return expression_statement(assign(target, value))

property_access = PropertyAccess = collections.namedtuple("PropertyAccess", ["value", "property"])
binary_operation = BinaryOperation = collections.namedtuple("BinaryOperation", ["operator", "left", "right"])
unary_operation = UnaryOperation = collections.namedtuple("UnaryOperation", ["operator", "operand"])
call = Call = collections.namedtuple("Call", ["func", "args"])
ref = VariableReference = collections.namedtuple("VariableReference", ["name"])
number = Number = collections.namedtuple("Number", ["value"])
NullLiteral = collections.namedtuple("NullLiteral", [])
null = NullLiteral()
boolean = Boolean = collections.namedtuple("Boolean", ["value"])
string = String = collections.namedtuple("String", ["value"])
array = Array = collections.namedtuple("Array", ["elements"])
obj = Object = collections.namedtuple("Object", ["properties"])

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
