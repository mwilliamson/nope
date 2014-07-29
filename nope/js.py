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
    fileobj.write("function ")
    fileobj.write(obj.name)
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
    fileobj.write(";")


def _serialize_assignment(obj, fileobj):
    fileobj.write(obj.name)
    fileobj.write(" = ")
    dump(obj.value, fileobj)


def _serialize_property_access(obj, fileobj):
    fileobj.write("(")
    dump(obj.value, fileobj)
    fileobj.write(").")
    fileobj.write(obj.property)


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


def _serialize_string(obj, fileobj):
    json.dump(obj.value, fileobj)


def _serialize_array(obj, fileobj):
    fileobj.write("[")
    
    for index, arg in enumerate(obj.elements):
        if index > 0:
            fileobj.write(", ");
        dump(arg, fileobj)
    
    fileobj.write("]")

statements = Statements = collections.namedtuple("Statements", ["statements"])

expression_statement = ExpressionStatement = collections.namedtuple("ExpressionStatement", ["value"])
function_declaration = FunctionDeclaration = collections.namedtuple("FunctionDeclaration", ["name", "args", "body"])
ret = ReturnStatement = collections.namedtuple("ReturnStatement", ["value"])
var = VariableDeclaration = collections.namedtuple("VariableDeclaration", ["name"])

assign = Assignment = collections.namedtuple("Assignment", ["name", "value"])
property_access = PropertyAccess = collections.namedtuple("PropertyAccess", ["value", "property"])
call = Call = collections.namedtuple("Call", ["func", "args"])
ref = VariableReference = collections.namedtuple("VariableReference", ["name"])
number = Number = collections.namedtuple("Number", ["value"])
NullLiteral = collections.namedtuple("NullLiteral", [])
null = NullLiteral()
string = String = collections.namedtuple("String", ["value"])
array = Array = collections.namedtuple("Array", ["elements"])

_serializers = {
    Statements: _serialize_statements,
    
    ExpressionStatement: _serialize_expression_statement,
    FunctionDeclaration: _serialize_function_declaration,
    ReturnStatement: _serialize_return_statement,
    VariableDeclaration: _serialize_variable_declaration,
    
    Assignment: _serialize_assignment,
    PropertyAccess: _serialize_property_access,
    Call: _serialize_call,
    VariableReference: _serialize_ref,
    Number: _serialize_number,
    NullLiteral: _serialize_null,
    String: _serialize_string,
    Array: _serialize_array,
}
