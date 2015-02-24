import sys

import dodge


def _create_node(name, fields):
    fields = fields[:]
    fields.append(dodge.field("explicit_type", default=None, show_default=False))
    
    return dodge.data_class(name, fields)


NoneLiteral = _create_node("NoneLiteral", [])
BooleanLiteral = _create_node("BooleanLiteral", ["value"])
IntLiteral = _create_node("IntLiteral", ["value"])
StringLiteral = _create_node("StringLiteral", ["value"])
TupleLiteral = _create_node("TupleLiteral", ["elements"])
ListLiteral = _create_node("ListLiteral", ["elements"])
DictLiteral = _create_node("DictLiteral", ["items"])
VariableReference = _create_node("VariableReference", ["name"])

Call = _create_node("Call", ["func", "args", "kwargs"])
AttributeAccess = _create_node("AttributeAccess", ["value", "attr"])
TypeApplication = _create_node("TypeApplication", ["generic_type", "params"])
TypeUnion = _create_node("TypeUnion", ["types"])

unary_operation = UnaryOperation = _create_node("UnaryOperation", ["operator", "operand"])

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


binary_operation = BinaryOperation = _create_node("BinaryOperation", ["operator", "left", "right"])

binary_operators = [
    "add", "sub", "mul", "truediv", "floordiv", "mod", "pow",
    "lshift", "rshift", "and", "xor", "or",
    "eq", "ne", "lt", "le", "gt", "ge",
    "bool_and", "bool_or",
    "is", "is_not",
    "contains",
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

subscript = Subscript = _create_node("Subscript", ["value", "slice"])
slice = Slice = _create_node("Slice", ["start", "stop", "step"])

list_comprehension = ListComprehension = _create_node("ListComprehension", ["element", "generator"])
generator_expression = GeneratorExpression = _create_node("GeneratorExpression", ["element", "generator"])
comprehension = Comprehension = _create_node("Comprehension", ["target", "iterable"])

ReturnStatement = _create_node("ReturnStatement", ["value"])
ExpressionStatement = _create_node("ExpressionStatement", ["value"])
Assignment = _create_node("Assignment", ["targets", "value"])
IfElse = _create_node("IfElse", ["condition", "true_body", "false_body"])
WhileLoop = _create_node("WhileLoop", ["condition", "body", "else_body"])
ForLoop = _create_node("ForLoop", ["target", "iterable", "body", "else_body"])
BreakStatement = _create_node("BreakStatement", [])
ContinueStatement = _create_node("ContinueStatement", [])
TryStatement = _create_node("TryStatement", ["body", "handlers", "finally_body"])
ExceptHandler = _create_node("ExceptHandler", ["type", "target", "body"])
RaiseStatement = _create_node("RaiseStatement", ["value"])
AssertStatement = _create_node("AssertStatement", ["condition", "message"])
WithStatement = _create_node("WithStatement", ["value", "target", "body"])

FunctionDef = _create_node("FunctionDef", ["name", "args", "body"])
FunctionSignature = _create_node("FunctionSignature", ["type_params", "args", "returns"])
SignatureArgument = _create_node("SignatureArgument", ["name", "type", "optional"])
Arguments = _create_node("Arguments", ["args"])
Argument = _create_node("Argument", ["name", "optional"])

ClassDefinition = _create_node("ClassDefinition", ["name", "body", "base_classes", "type_params"])
FormalTypeParameter = _create_node("FormalTypeParameter", ["name"])
TypeDefinition = _create_node("TypeDefinition", ["name", "value"])

Import = _create_node("Import", ["names"])
ImportFrom = _create_node("ImportFrom", ["module", "names"])
class ImportAlias(_create_node("ImportAlias", ["name", "asname"])):
    @property
    def value_name(self):
        if self.asname is None:
            return self.name_parts[0]
        else:
            return self.asname
    
    @property
    def name_parts(self):
        return self.name.split(".")

Module = _create_node("Module", ["body", "is_executable"])
Statements = _create_node("Statements", ["body"])

def none():
    return NoneLiteral()


def int(value):
    return IntLiteral(value)

int_literal = int

boolean = BooleanLiteral
string = StringLiteral
tuple_literal = TupleLiteral
list_literal = ListLiteral
dict_literal = DictLiteral
ref = VariableReference

def call(func, args, kwargs=None):
    if kwargs is None:
        kwargs = {}
    
    return Call(func, args, kwargs)

attr = AttributeAccess
type_apply = TypeApplication
type_union = TypeUnion

ret = ReturnStatement
expression_statement = ExpressionStatement


def assign(targets, value, *, explicit_type=None):
    target_nodes = [
        ref(target) if isinstance(target, str) else target
        for target in targets
    ]
    return Assignment(target_nodes, value, explicit_type=explicit_type)


if_ = IfElse

def for_loop(target, iterable, body, else_body=None):
    if else_body is None:
        else_body = []
    
    return ForLoop(target, iterable, body, else_body)


def while_(condition, body, else_body=None):
    if else_body is None:
        else_body = []
    
    return WhileLoop(condition, body, else_body)

break_ = BreakStatement
continue_ = ContinueStatement

def try_(body, *, handlers=None, finally_body=None):
    if handlers is None:
        handlers = []
    if finally_body is None:
        finally_body = []
    return TryStatement(body, handlers, finally_body)


def except_(type, target, body):
    if isinstance(target, str):
        target = ref(target)
    
    return ExceptHandler(type, target, body)

raise_statement = RaiseStatement

def assert_statement(condition, message=None):
    return AssertStatement(condition, message)


with_statement = WithStatement


def typed(type_, node):
    return dodge.copy(node, explicit_type=type_)


def explicit_type_of(node):
    if node is None:
        return None
    else:
        return node.explicit_type


def func(name, args, body):
    return FunctionDef(name, args, body)


def class_(name, body, *, base_classes=None, type_params=None):
    if base_classes is None:
        base_classes = []
    
    if type_params is None:
        type_params = []
    
    return ClassDefinition(name, body, base_classes=base_classes, type_params=type_params)


formal_type_parameter = FormalTypeParameter


type_definition = TypeDefinition


def signature(*, type_params=None, args=None, returns=None):
    if type_params is None:
        type_params = []
    
    if args is None:
        args = []
    
    if returns is None:
        returns = None
    
    return FunctionSignature(type_params=type_params, args=args, returns=returns)


def signature_arg(name, type_=None, optional=False):
    if type_ is None:
        type_ = name
        name = None
    
    return SignatureArgument(name, type_, optional=optional)

args = arguments = Arguments

def argument(name, optional=False):
    return Argument(name, optional=optional)

arg = argument

import_from = ImportFrom
import_alias = ImportAlias

def module(body, is_executable=False):
    return Module(body, is_executable)
