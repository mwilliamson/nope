import io
import functools

import dodge


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
            
            TryStatement: self._try,
            ExceptHandler: self._except,
            
            ExpressionStatement: self._expression_statement,
            Assignment: self._assignment,
            ReturnStatement: self._return,
            RaiseStatement: self._raise,
            
            Call: self._call,
            AttributeAccess: self._attr,
            UnaryOperation: self._unary_operation,
            
            BuiltinReference: self._builtin,
            VariableReference: self._ref,
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
    
    def _builtin(self, node):
        self._output.write("$builtins." + node.name)
    
    def _ref(self, node):
        self._output.write(node.name)
    
    def _bool(self, node):
        self._output.write(str(node.value))
    
    def _none(self, node):
        self._output.write("None")


module = Module = dodge.data_class("Module", ["body", "is_executable"])

statements = Statements = dodge.data_class("Statements", ["body"])

try_ = TryStatement = dodge.data_class("TryStatement", ["body", "handlers", "finally_body"])
except_ = ExceptHandler = dodge.data_class("ExceptHandler", ["type", "target", "body"])

if_ = IfStatement = dodge.data_class("IfStatement", ["condition", "true_body", "false_body"])

func = FunctionDefinition = dodge.data_class("FunctionDefinition", ["name", "args", "body"])
arg = FormalArgument = dodge.data_class("FormalArgument", ["name"])

expression_statement = ExpressionStatement = dodge.data_class("ExpressionStatement", ["value"])
assign = Assignment = dodge.data_class("Assignment", ["target", "value"])
ret = ReturnStatement = dodge.data_class("ReturnStatement", ["value"])
RaiseStatement = dodge.data_class("RaiseStatement", [])

def raise_():
    return RaiseStatement()

call = Call = dodge.data_class("Call", ["func", "args"])
attr = AttributeAccess = dodge.data_class("AttributeAccess", ["obj", "attr"])
UnaryOperation = dodge.data_class("UnaryOperation", ["operator", "operand"])

def not_(operand):
    return UnaryOperation("not", operand)

builtin = BuiltinReference = dodge.data_class("BuiltinReference", ["name"])
ref = VariableReference = dodge.data_class("VariableReference", ["name"])
BooleanLiteral = dodge.data_class("BooleanLiteral", ["value"])
false = BooleanLiteral(False)
true = BooleanLiteral(True)
NoneLiteral = dodge.data_class("NoneLiteral", [])
none = NoneLiteral()
