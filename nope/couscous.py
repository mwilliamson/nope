import io
import functools

import dodge

from . import nodes


def dumps(node):
    output = io.StringIO()
    dump(node, output)
    return output.getvalue()


def dump(node, output):
    writer = Writer(output)
    writer.write(node)


def _simple_statement(func):
    @functools.wraps(func)
    def wrapped(self, node):
        self._indent()
        func(self, node)
        self._output.write("\n")
    
    return wrapped


class Writer(object):
    def __init__(self, output):
        self._output = output
        self._indentation = 0
        self._writers = {
            Statements: self._statements,
            
            IfStatement: self._if,
            WhileLoop: self._while,
            BreakStatement: self._break,
            
            TryStatement: self._try,
            ExceptHandler: self._except,
            
            ExpressionStatement: self._expression_statement,
            VariableDeclaration: self._declaration,
            Assignment: self._assignment,
            ReturnStatement: self._return,
            RaiseStatement: self._raise,
            
            Call: self._call,
            AttributeAccess: self._attr,
            UnaryOperation: self._unary_operation,
            BinaryOperation: self._binary_operation,
            
            BuiltinReference: self._builtin,
            InternalReference: self._internal,
            VariableReference: self._ref,
            StrLiteral: self._str,
            IntLiteral: self._int,
            BooleanLiteral: self._bool,
            NoneLiteral: self._none,
        }
    
    def write(self, node):
        return self._writers[type(node)](node)
    
    def _write_statements(self, statements):
        for statement in statements:
            self.write(statement)
    
    def _statements(self, node):
        self._write_statements(node.body)
    
    def _try(self, node):
        self._indent()
        self._output.write("try")
        
        self._write_block(node.body)
        
        for handler in node.handlers:
            self.write(handler)
        
        self._indent()
        self._output.write("finally")
        self._write_block(node.finally_body)
    
    def _except(self, node):
        self._indent()
        self._output.write("except ")
        self.write(node.type)
        if node.target:
            self._output.write(" as ")
            self.write(node.target)
        
        self._write_block(node.body)
    
    def _if(self, node):
        self._indent()
        self._output.write("if ")
        self.write(node.condition)
        self._write_block(node.true_body)
    
    def _while(self, node):
        self._indent()
        self._output.write("while ")
        self.write(node.condition)
        self._write_block(node.body)
    
    @_simple_statement
    def _break(self, node):
        self._output.write("break")
    
    def _indent(self):
        self._output.write("    " * self._indentation)
    
    def _write_block(self, statements):
        self._start_block()
        self._write_statements(statements)
        self._end_block()
    
    def _start_block(self):
        self._indentation += 1
        self._output.write(":\n")
    
    def _end_block(self):
        self._indentation -= 1
    
    @_simple_statement
    def _expression_statement(self, node):
        self.write(node.value)
    
    @_simple_statement
    def _declaration(self, node):
        self._output.write("var ")
        self._output.write(node.name)
        if node.value is not None:
            self._output.write(" = ")
            self.write(node.value)
    
    @_simple_statement
    def _assignment(self, node):
        self.write(node.target)
        self._output.write(" = ")
        self.write(node.value)
    
    @_simple_statement
    def _return(self, node):
        self._output.write("return ")
        self.write(node.value)
    
    @_simple_statement
    def _raise(self, node):
        self._output.write("raise")
        if node.value is not None:
            self._output.write(" ")
            self.write(node.value)
    
    def _call(self, node):
        self.write(node.func)
        self._output.write("(")
        
        for index, arg in enumerate(node.args):
            if index > 0:
                self._output.write(", ")
            
            self.write(arg)
        
        self._output.write(")")
    
    def _attr(self, node):
        self.write(node.obj)
        self._output.write(".")
        self._output.write(node.attr)
    
    def _unary_operation(self, node):
        self._output.write(node.operator)
        self._output.write(" ")
        self.write(node.operand)
    
    def _binary_operation(self, node):
        self.write(node.left)
        self._output.write(" ")
        self._output.write(node.operator)
        self._output.write(" ")
        self.write(node.right)
    
    def _builtin(self, node):
        self._output.write("$builtins." + node.name)
    
    def _internal(self, node):
        self._output.write("$internals." + node.name)
    
    def _ref(self, node):
        self._output.write(node.name)
    
    def _str(self, node):
        self._output.write('"')
        self._output.write(node.value)
        self._output.write('"')
    
    def _int(self, node):
        self._output.write(str(node.value))
    
    def _bool(self, node):
        self._output.write(str(node.value))
    
    def _none(self, node):
        self._output.write("None")


def module(body, is_executable=False, exported_names=None):
    if exported_names is None:
        exported_names = []
    
    return Module(body, is_executable, exported_names)

Module = dodge.data_class("Module", ["body", "is_executable", "exported_names"])
module_ref = ModuleReference = dodge.data_class("ModuleReference", ["names"])

# TODO: create import nodes for couscous
import_from = ImportFrom = nodes.import_from
import_alias = ImportAlias = nodes.import_alias

def statements(body):
    if len(body) == 1:
        return body[0]
    else:
        return Statements(body)

Statements = dodge.data_class("Statements", ["body"])

def class_(name, *, methods, body, type_params=None):
    if type_params is None:
        type_params = []
    
    return ClassDefinition(name, methods, body, type_params)

ClassDefinition = dodge.data_class("ClassDefinition", ["name", "methods", "body", "type_params"])
formal_type_parameter = FormalTypeParameter = dodge.data_class("FormalTypeParameter", ["name"])
func = FunctionDefinition = dodge.data_class("FunctionDefinition", ["name", "args", "body"])
arg = FormalArgument = dodge.data_class("FormalArgument", ["name"])


def try_(body, handlers=None, finally_body=None):
    if handlers is None:
        handlers = []
    if finally_body is None:
        finally_body = []
    
    return TryStatement(body, handlers, finally_body)

TryStatement = dodge.data_class("TryStatement", ["body", "handlers", "finally_body"])
except_ = ExceptHandler = dodge.data_class("ExceptHandler", ["type", "target", "body"])

def if_(condition, true_body, false_body=None):
    if false_body is None:
        false_body = []
    
    return IfStatement(condition, true_body, false_body)

IfStatement = dodge.data_class("IfStatement", ["condition", "true_body", "false_body"])
while_ = WhileLoop = dodge.data_class("WhileLoop", ["condition", "body"])
BreakStatement = dodge.data_class("BreakStatement", [])
break_ = BreakStatement()
ContinueStatement = dodge.data_class("ContinueStatement", [])
continue_ = ContinueStatement()

expression_statement = ExpressionStatement = dodge.data_class("ExpressionStatement", ["value"])
assign = Assignment = dodge.data_class("Assignment", ["target", "value"])

def declare(name, value=None):
    return VariableDeclaration(name, value)

VariableDeclaration = dodge.data_class("VariableDeclaration", ["name", "value"])

ret = ReturnStatement = dodge.data_class("ReturnStatement", ["value"])
RaiseStatement = dodge.data_class("RaiseStatement", ["value"])

def raise_(value=None):
    return RaiseStatement(value)

function_expression = FunctionExpression = dodge.data_class("FunctionExpression", ["args", "body"])

call = Call = dodge.data_class("Call", ["func", "args"])
attr = AttributeAccess = dodge.data_class("AttributeAccess", ["obj", "attr"])

UnaryOperation = dodge.data_class("UnaryOperation", ["operator", "operand"])
not_ = functools.partial(UnaryOperation, "not")

BinaryOperation = dodge.data_class("BinaryOperation", ["operator", "left", "right"])
is_ = functools.partial(BinaryOperation, "is")
is_not = functools.partial(BinaryOperation, "is_not")
and_ = functools.partial(BinaryOperation, "and")
or_ = functools.partial(BinaryOperation, "or")

ternary_conditional = TernaryConditional = dodge.data_class("TernaryConditional", ["condition", "true_value", "false_value"])

list_literal = ListLiteral = dodge.data_class("ListLiteral", ["elements"])
tuple_literal = TupleLiteral = dodge.data_class("TupleLiteral", ["elements"])

builtin = BuiltinReference = dodge.data_class("BuiltinReference", ["name"])
internal = InternalReference = dodge.data_class("InternalReference", ["name"])
ref = VariableReference = dodge.data_class("VariableReference", ["name"])
str_literal = StrLiteral = dodge.data_class("StrLiteral", ["value"])
int_literal = IntLiteral = dodge.data_class("IntLiteral", ["value"])
bool_literal = BooleanLiteral = dodge.data_class("BooleanLiteral", ["value"])
false = BooleanLiteral(False)
true = BooleanLiteral(True)
NoneLiteral = dodge.data_class("NoneLiteral", [])
none = NoneLiteral()
