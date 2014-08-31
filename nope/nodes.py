import sys

import dodge


NoneExpression = dodge.data_class("NoneExpression", [])
BooleanExpression = dodge.data_class("BooleanExpression", ["value"])
IntExpression = dodge.data_class("IntExpression", ["value"])
StringExpression = dodge.data_class("StringExpression", ["value"])
ListExpression = dodge.data_class("ListExpression", ["elements"])
VariableReference = dodge.data_class("VariableReference", ["name"])

Call = dodge.data_class("Call", ["func", "args", "kwargs"])
AttributeAccess = dodge.data_class("AttributeAccess", ["value", "attr"])
TypeApplication = dodge.data_class("TypeApplication", ["generic_type", "params"])

unary_operation = UnaryOperation = dodge.data_class("UnaryOperation", ["operator", "operand"])

unary_operators = ["neg", "pos", "invert", "bool_not"]


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


binary_operation = BinaryOperation = dodge.data_class("BinaryOperation", ["operator", "left", "right"])

binary_operators = [
    "add", "sub", "mul", "truediv", "floordiv", "mod", "pow",
    "lshift", "rshift", "and", "xor", "or",
    "eq", "ne", "lt", "le", "gt", "ge",
    "bool_and", "bool_or",
    "is",
]


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

subscript = Subscript = dodge.data_class("Subscript", ["value", "slice"])

ReturnStatement = dodge.data_class("ReturnStatement", ["value"])
ExpressionStatement = dodge.data_class("ExpressionStatement", ["value"])
Assignment = dodge.data_class("Assignment", ["targets", "value"])
IfElse = dodge.data_class("IfElse", ["condition", "true_body", "false_body"])
WhileLoop = dodge.data_class("WhileLoop", ["condition", "body", "else_body"])
ForLoop = dodge.data_class("ForLoop", ["target", "iterable", "body", "else_body"])
BreakStatement = dodge.data_class("BreakStatement", [])
ContinueStatement = dodge.data_class("ContinueStatement", [])
TryStatement = dodge.data_class("TryStatement", ["body", "handlers", "finally_body"])
ExceptHandler = dodge.data_class("ExceptHandler", ["type", "target", "body"])
RaiseStatement = dodge.data_class("RaiseStatement", ["value"])
AssertStatement = dodge.data_class("AssertStatement", ["condition", "message"])
WithStatement = dodge.data_class("WithStatement", ["value", "target", "body"])

FunctionDef = dodge.data_class("FunctionDef", ["name", "signature", "args", "body"])
FunctionSignature = dodge.data_class("FunctionSignature", ["type_params", "args", "returns"])
SignatureArgument = dodge.data_class("SignatureArgument", ["name", "type"])
Arguments = dodge.data_class("Arguments", ["args"])
Argument = dodge.data_class("Argument", ["name"])

ClassDef = dodge.data_class("ClassDef", ["name", "body"])

Import = dodge.data_class("Import", ["names"])
ImportFrom = dodge.data_class("ImportFrom", ["module", "names"])
class ImportAlias(dodge.data_class("ImportAlias", ["name", "asname"])):
    @property
    def value_name(self):
        if self.asname is None:
            return self.name_parts[0]
        else:
            return self.asname
    
    @property
    def name_parts(self):
        return self.name.split(".")

Module = dodge.data_class("Module", ["body", "is_executable"])


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


def except_handler(type, target, body):
    if isinstance(target, str):
        target = ref(target)
    
    return ExceptHandler(type, target, body)

raise_statement = RaiseStatement

def assert_statement(condition, message=None):
    return AssertStatement(condition, message)


with_statement = WithStatement


def func(name, signature, args, body):
    return FunctionDef(name, signature, args, body)


class_def = ClassDef


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
