import collections


NoneExpression = collections.namedtuple("NoneExpression", [])
BooleanExpression = collections.namedtuple("BooleanExpression", ["value"])
IntExpression = collections.namedtuple("IntExpression", ["value"])
StringExpression = collections.namedtuple("StringExpression", ["value"])
ListExpression = collections.namedtuple("ListExpression", ["elements"])
VariableReference = collections.namedtuple("VariableReference", ["name"])

Call = collections.namedtuple("Call", ["func", "args"])
AttributeAccess = collections.namedtuple("AttributeAccess", ["value", "attr"])
TypeApplication = collections.namedtuple("TypeApplication", ["generic_type", "params"])

ReturnStatement = collections.namedtuple("ReturnStatement", ["value"])
ExpressionStatement = collections.namedtuple("ExpressionStatement", ["value"])
Assignment = collections.namedtuple("Assignment", ["targets", "value"])
IfElse = collections.namedtuple("IfElse", ["condition", "true_body", "false_body"])

FunctionDef = collections.namedtuple("FunctionDef", ["name", "args", "return_annotation", "body", "type_params"])
Arguments = collections.namedtuple("Arguments", ["args"])
Argument = collections.namedtuple("Argument", ["name", "annotation"])

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
str = StringExpression
list = ListExpression
ref = VariableReference

call = Call
attr = AttributeAccess
type_apply = TypeApplication

ret = ReturnStatement
expression_statement = ExpressionStatement
assign = Assignment
if_else = IfElse

def func(name, args, return_annotation, body, type_params=None):
    if type_params is None:
        type_params = []
    
    return FunctionDef(name, args, return_annotation, body, type_params)

    
args = arguments = Arguments
arg = argument = Argument

import_from = ImportFrom
import_alias = ImportAlias

def module(body, is_executable=False):
    return Module(body, is_executable)


binary_operation = BinaryOperation = collections.namedtuple("BinaryOperation", ["operator", "left", "right"])

binary_operators = ["add"]


def _create_boolean_operators():
    import sys
    for operator in binary_operators:
        def create(left, right):
            return BinaryOperation(operator, left, right)
        
        name = operator
        create.__name__ = name
        setattr(sys.modules[__name__], name, create)

_create_boolean_operators()
