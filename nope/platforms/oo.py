import json

import dodge


statements = Statements = dodge.data_class("Statements", ["statements"])

if_ = IfElse = dodge.data_class("IfElse", ["condition", "true_body", "false_body"])
while_ = WhileLoop = dodge.data_class("WhileLoop", ["condition", "body"])
BreakStatement = dodge.data_class("BreakStatement", [])
ContinueStatement = dodge.data_class("ContinueStatement", [])

break_ = BreakStatement()
continue_ = ContinueStatement()

throw = Throw = dodge.data_class("Throw", ["value"])

expression_statement = ExpressionStatement = dodge.data_class("ExpressionStatement", ["value"])
ret = ReturnStatement = dodge.data_class("ReturnStatement", ["value"])


AssignmentExpression = dodge.data_class("AssignmentExpression", ["target", "value"])

def assignment_expression(target, value):
    if isinstance(target, str):
        target = ref(target)
    
    return AssignmentExpression(target, value)

property_access = PropertyAccess = dodge.data_class("PropertyAccess", ["value", "property"])
binary_operation = BinaryOperation = dodge.data_class("BinaryOperation", ["operator", "left", "right"])
unary_operation = UnaryOperation = dodge.data_class("UnaryOperation", ["operator", "operand"])
ternary_conditional = TernaryConditional = dodge.data_class("TernaryConditional", ["condition", "true_value", "false_value"])
call = Call = dodge.data_class("Call", ["func", "args"])
ref = VariableReference = dodge.data_class("VariableReference", ["name"])
integer_literal = IntegerLiteral = dodge.data_class("IntegerLiteral", ["value"])
number = Number = dodge.data_class("Number", ["value"])
NullLiteral = dodge.data_class("NullLiteral", [])
null = NullLiteral()
boolean = Boolean = dodge.data_class("Boolean", ["value"])
string = String = dodge.data_class("String", ["value"])


class Writer(object):
    def __init__(self, serializers, fileobj, **kwargs):
        self._fileobj = fileobj
        self._serializers = serializers
        self._pretty_print = kwargs.pop("pretty_print", True)
        self._indentation = 0
        self._pending_indentation = False
        assert not kwargs
    
    def write(self, value):
        if self._pending_indentation:
            self._fileobj.write(" " * (self._indentation * 4))
            self._pending_indentation = False
        
        self._fileobj.write(value)
    
    def dump(self, node):
        self._serializers[type(node)](node, self)
    
    def newline(self):
        if self._pretty_print:
            self.write("\n")
            self._pending_indentation = True
    
    def dump_block(self, statements):
        self.start_block()
        for statement in statements:
            self.dump(statement)
        self.end_block()
    
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
        else:
            self.write(" }")
    
    def end_simple_statement(self):
        self.write(";")
        self.newline()
    
    def end_compound_statement(self):
        self.newline()


def _serialize_statements(obj, writer):
    for statement in obj.statements:
        writer.dump(statement)


def _serialize_if_else(obj, writer):
    writer.write("if (")
    writer.dump(obj.condition)
    writer.write(") ")
    
    writer.dump_block(obj.true_body)
    if obj.false_body:
        writer.write(" else ")
        writer.dump_block(obj.false_body)
    
    writer.end_compound_statement()


def _serialize_while_loop(obj, writer):
    writer.write("while (")
    writer.dump(obj.condition)
    writer.write(") ")
    writer.dump_block(obj.body)
    writer.end_compound_statement()


def _serialize_break_statement(obj, writer):
    writer.write("break")
    writer.end_simple_statement()


def _serialize_continue_statement(obj, writer):
    writer.write("continue")
    writer.end_simple_statement()


def _serialize_throw(obj, writer):
    writer.write("throw")
    
    if obj.value is not None:
        writer.write(" ")
        writer.dump(obj.value)
    
    writer.end_simple_statement()


def _serialize_expression_statement(obj, writer):
    writer.dump(obj.value)
    writer.end_simple_statement()


def _serialize_return_statement(obj, writer):
    writer.write("return ")
    writer.dump(obj.value)
    writer.end_simple_statement()


def _serialize_assignment_expression(obj, writer):
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


def _serialize_ternary_conditional(node, writer):
    writer.dump(node.condition)
    writer.write(" ? ")
    writer.dump(node.true_value)
    writer.write(" : ")
    writer.dump(node.false_value)


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


def _serialize_literal_value(obj, writer):
    writer.write(str(obj.value))


def _serialize_null(obj, writer):
    writer.write("null")


def _serialize_boolean(obj, writer):
    serialized_value = "true" if obj.value else "false"
    writer.write(serialized_value)


def _serialize_string(obj, writer):
    json.dump(obj.value, writer)


_default_serializers = {
    Statements: _serialize_statements,
    
    IfElse: _serialize_if_else,
    WhileLoop: _serialize_while_loop,
    BreakStatement: _serialize_break_statement,
    ContinueStatement: _serialize_continue_statement,
    
    Throw: _serialize_throw,
    
    ExpressionStatement: _serialize_expression_statement,
    ReturnStatement: _serialize_return_statement,
    
    AssignmentExpression: _serialize_assignment_expression,
    PropertyAccess: _serialize_property_access,
    BinaryOperation: _serialize_binary_operation,
    UnaryOperation: _serialize_unary_operation,
    TernaryConditional: _serialize_ternary_conditional,
    Call: _serialize_call,
    VariableReference: _serialize_ref,
    Number: _serialize_literal_value,
    IntegerLiteral: _serialize_literal_value,
    NullLiteral: _serialize_null,
    Boolean: _serialize_boolean,
    String: _serialize_string,
}


def serializers(others):
    serializers = _default_serializers.copy()
    serializers.update(others)
    return serializers
