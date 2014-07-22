import collections
import io


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


statements = Statements = collections.namedtuple("Statements", ["statements"])
expression_statement = ExpressionStatement = collections.namedtuple("ExpressionStatement", ["value"])
call = Call = collections.namedtuple("Call", ["func", "args"])
ref = VariableReference = collections.namedtuple("VariableReference", ["name"])
number = Number = collections.namedtuple("Number", ["value"])

_serializers = {
    Statements: _serialize_statements,
    ExpressionStatement: _serialize_expression_statement,
    Call: _serialize_call,
    VariableReference: _serialize_ref,
    Number: _serialize_number,
}
