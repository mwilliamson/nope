import json
import contextlib

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

def assignment_expression(target, value):
    if isinstance(target, str):
        target = ref(target)
    
    return binary_operation("=", target, value)

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
        self._precedence_stack = [None]
        assert not kwargs
    
    @contextlib.contextmanager
    def precedence(self, precedence):
        self._precedence_stack.append(precedence)
        try:
            yield
        finally:
            self._precedence_stack.pop()
        
    
    def write(self, value):
        if self._pending_indentation:
            self._fileobj.write(" " * (self._indentation * 4))
            self._pending_indentation = False
        
        self._fileobj.write(value)
    
    def dump(self, node):
        serializer = self._serializers[type(node)]
        serialize_method = getattr(serializer, "serialize", None)
        
        if serialize_method is None:
            serialize = serializer
            node_precedence = None
        else:
            serialize = serialize_method
            node_precedence = serializer.precedence(node)
            
        needs_parens = (
            self._precedence_stack[-1] is not None and
            node_precedence is not None and
            node_precedence <= self._precedence_stack[-1]
        )
        
        if needs_parens:
            self.write("(")
            
        with self.precedence(node_precedence):
            serialize(node, self)
        
        if needs_parens:
            self.write(")")
    
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


class _PropertyAccessSerializer(object):
    def precedence(self, node):
        return 18
    
    def serialize(self, node, writer):
        writer.dump(node.value)
        if isinstance(node.property, str):
            writer.write(".")
            writer.write(node.property)
        else:
            writer.write("[")
            writer.dump(node.property)
            writer.write("]")


class _BinaryOperationSerializer(object):
    _precedences = {
        "*": 14,
        "/": 14,
        "%": 14,
        "+": 13,
        "-": 13,
        "<<": 12,
        ">>": 12,
        ">>>": 12,
        "<": 11,
        "<=": 11,
        ">": 11,
        ">=": 11,
        "==": 10,
        "!=": 10,
        "===": 10,
        "!==": 10,
        "&": 9,
        "^": 8,
        "|": 7,
        "&&": 6,
        "||": 5,
        "=": 3,
        
    }
    
    def precedence(self, node):
        return self._precedences[node.operator]
    
    def serialize(self, node, writer):
        writer.dump(node.left)
        writer.write(" ")
        writer.write(node.operator)
        writer.write(" ")
        writer.dump(node.right)


class _UnaryOperationSerializer(object):
    def precedence(self, node):
        return 15
    
    def serialize(self, obj, writer):
        writer.write(obj.operator)
        writer.dump(obj.operand)


class _TernaryConditionalSerializer(object):
    def precedence(self, node):
        return 4
    
    def serialize(self, node, writer):
        writer.dump(node.condition)
        writer.write(" ? ")
        writer.dump(node.true_value)
        writer.write(" : ")
        writer.dump(node.false_value)


class _CallSerializer(object):
    def precedence(self, node):
        return 17
    
    def serialize(self, obj, writer):
        writer.dump(obj.func)
        writer.write("(")
        
        with writer.precedence(None):
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
    
    PropertyAccess: _PropertyAccessSerializer(),
    BinaryOperation: _BinaryOperationSerializer(),
    UnaryOperation: _UnaryOperationSerializer(),
    TernaryConditional: _TernaryConditionalSerializer(),
    Call: _CallSerializer(),
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
