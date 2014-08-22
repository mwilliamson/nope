import collections
import sys


NoneExpression = collections.namedtuple("NoneExpression", [])
BooleanExpression = collections.namedtuple("BooleanExpression", ["value"])
IntExpression = collections.namedtuple("IntExpression", ["value"])
StringExpression = collections.namedtuple("StringExpression", ["value"])
ListExpression = collections.namedtuple("ListExpression", ["elements"])
VariableReference = collections.namedtuple("VariableReference", ["name"])

Call = collections.namedtuple("Call", ["func", "args", "kwargs"])
AttributeAccess = collections.namedtuple("AttributeAccess", ["value", "attr"])
TypeApplication = collections.namedtuple("TypeApplication", ["generic_type", "params"])

ReturnStatement = collections.namedtuple("ReturnStatement", ["value"])
ExpressionStatement = collections.namedtuple("ExpressionStatement", ["value"])
Assignment = collections.namedtuple("Assignment", ["targets", "value"])
IfElse = collections.namedtuple("IfElse", ["condition", "true_body", "false_body"])
WhileLoop = collections.namedtuple("WhileLoop", ["condition", "body", "else_body"])
ForLoop = collections.namedtuple("ForLoop", ["target", "iterable", "body", "else_body"])
BreakStatement = collections.namedtuple("BreakStatement", [])
ContinueStatement = collections.namedtuple("ContinueStatement", [])
TryStatement = collections.namedtuple("TryStatement", ["body", "handlers", "finally_body"])
ExceptHandler = collections.namedtuple("ExceptHandler", ["type", "name", "body"])
RaiseStatement = collections.namedtuple("RaiseStatement", ["value"])
AssertStatement = collections.namedtuple("AssertStatement", ["condition", "message"])
WithStatement = collections.namedtuple("WithStatement", ["value", "target", "body"])

FunctionDef = collections.namedtuple("FunctionDef", ["name", "signature", "args", "body"])
FunctionSignature = collections.namedtuple("FunctionSignature", ["type_params", "args", "returns"])
SignatureArgument = collections.namedtuple("SignatureArgument", ["name", "type"])
Arguments = collections.namedtuple("Arguments", ["args"])
Argument = collections.namedtuple("Argument", ["name"])

Import = collections.namedtuple("Import", ["names"])
ImportFrom = collections.namedtuple("ImportFrom", ["module", "names"])
class ImportAlias(collections.namedtuple("ImportAlias", ["name", "asname"])):
    @property
    def value_name(self):
        if self.asname is None:
            return self.name_parts[0]
        else:
            return self.asname
    
    @property
    def name_parts(self):
        return self.name.split(".")

Module = collections.namedtuple("Module", ["body", "is_executable"])


def none():
    return NoneExpression()


def int(value):
    return IntExpression(value)

boolean = BooleanExpression
string = StringExpression
list = ListExpression
ref = VariableReference

def call(func, args, kwargs=None):
    if kwargs is None:
        kwargs = {}
    
    return Call(func, args, kwargs)

attr = AttributeAccess
type_apply = TypeApplication

ret = ReturnStatement
expression_statement = ExpressionStatement


def assign(targets, value):
    target_nodes = [
        ref(target) if isinstance(target, str) else target
        for target in targets
    ]
    return Assignment(target_nodes, value)


if_else = IfElse

def for_loop(target, iterable, body, else_body=None):
    if else_body is None:
        else_body = []
    
    return ForLoop(target, iterable, body, else_body)


def while_loop(condition, body, else_body=None):
    if else_body is None:
        else_body = []
    
    return WhileLoop(condition, body, else_body)

break_statement = BreakStatement
continue_statement = ContinueStatement

def try_statement(body, *, handlers=None, finally_body=None):
    if handlers is None:
        handlers = []
    if finally_body is None:
        finally_body = []
    return TryStatement(body, handlers, finally_body)


except_handler = ExceptHandler

raise_statement = RaiseStatement

def assert_statement(condition, message=None):
    return AssertStatement(condition, message)


with_statement = WithStatement


def func(name, signature, args, body):
    return FunctionDef(name, signature, args, body)


def signature(*, type_params=None, args=None, returns=None):
    if type_params is None:
        type_params = []
    
    if args is None:
        args = []
    
    if returns is None:
        returns = None
    
    return FunctionSignature(type_params=type_params, args=args, returns=returns)


def signature_arg(name, type_=None):
    if type_ is None:
        type_ = name
        name = None
    
    return SignatureArgument(name, type_)

args = arguments = Arguments
arg = argument = Argument

import_from = ImportFrom
import_alias = ImportAlias

def module(body, is_executable=False):
    return Module(body, is_executable)


unary_operation = UnaryOperation = collections.namedtuple("UnaryOperation", ["operator", "operand"])

unary_operators = ["neg", "pos", "invert"]


def _create_unary_operators():
    def _create_unary_operator(operator):
        def create(operand):
            return UnaryOperation(operator, operand)
        
        name = operator
        create.__name__ = name
        setattr(sys.modules[__name__], name, create)
        
    for operator in unary_operators:
        _create_unary_operator(operator)

_create_unary_operators()


binary_operation = BinaryOperation = collections.namedtuple("BinaryOperation", ["operator", "left", "right"])

binary_operators = ["add", "sub", "mul", "truediv", "floordiv", "mod", "pow", "lshift", "rshift", "and", "xor", "or"]


def _create_binary_operators():
    def _create_binary_operator(operator):
        def create(left, right):
            return BinaryOperation(operator, left, right)
        
        name = operator
        create.__name__ = name
        setattr(sys.modules[__name__], name, create)
        setattr(sys.modules[__name__], name + "_", create)
        
    for operator in binary_operators:
        _create_binary_operator(operator)

_create_binary_operators()

subscript = Subscript = collections.namedtuple("Subscript", ["value", "slice"])
