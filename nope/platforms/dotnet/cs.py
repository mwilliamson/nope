import dodge

statements = Statements = dodge.data_class("Statements", ["statements"])

expression_statement = ExpressionStatement = dodge.data_class("ExpressionStatement", ["value"])

call = Call = dodge.data_class("Call", ["func", "args"])
ref = VariableReference = dodge.data_class("VariableReference", ["name"])
integer_literal = IntegerLiteral = dodge.data_class("Integer", ["value"])


def dump(node, fileobj):
    return _writers[type(node)](node, fileobj)


def _write_statements(node, fileobj):
    for statement in node.statements:
        dump(statement, fileobj)


def _write_expression_statement(statement, fileobj):
    dump(statement.value, fileobj);
    fileobj.write(";\n")


def _write_call(call, fileobj):
    dump(call.func, fileobj)
    fileobj.write("(")
    
    for index, arg in enumerate(call.args):
        if index > 0:
            fileobj.write(", ");
        dump(arg, fileobj)
    
    fileobj.write(")")

    
def _write_variable_reference(reference, fileobj):
    fileobj.write(reference.name)


def _write_integer_literal(literal, fileobj):
    fileobj.write(str(literal.value))


_writers = {
    Statements: _write_statements,
    
    ExpressionStatement: _write_expression_statement,
    
    Call: _write_call,
    VariableReference: _write_variable_reference,
    IntegerLiteral: _write_integer_literal,
}
