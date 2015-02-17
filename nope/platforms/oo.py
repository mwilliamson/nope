import json

import dodge


property_access = PropertyAccess = dodge.data_class("PropertyAccess", ["value", "property"])
binary_operation = BinaryOperation = dodge.data_class("BinaryOperation", ["operator", "left", "right"])
unary_operation = UnaryOperation = dodge.data_class("UnaryOperation", ["operator", "operand"])
call = Call = dodge.data_class("Call", ["func", "args"])
ref = VariableReference = dodge.data_class("VariableReference", ["name"])
integer_literal = IntegerLiteral = dodge.data_class("IntegerLiteral", ["value"])
number = Number = dodge.data_class("Number", ["value"])
NullLiteral = dodge.data_class("NullLiteral", [])
null = NullLiteral()
boolean = Boolean = dodge.data_class("Boolean", ["value"])
string = String = dodge.data_class("String", ["value"])


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


_default_serializers = {
    PropertyAccess: _serialize_property_access,
    BinaryOperation: _serialize_binary_operation,
    UnaryOperation: _serialize_unary_operation,
    Call: _serialize_call,
    VariableReference: _serialize_ref,
    Number: _serialize_number,
    NullLiteral: _serialize_null,
    Boolean: _serialize_boolean,
    String: _serialize_string,
}


def serializers(others):
    serializers = _default_serializers.copy()
    serializers.update(others)
    return serializers
