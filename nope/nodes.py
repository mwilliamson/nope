import ast
import collections


NoneExpression = collections.namedtuple("NoneExpression", [])
IntExpression = collections.namedtuple("IntExpression", ["value"])
StringExpression = collections.namedtuple("StringExpression", ["value"])
VariableReference = collections.namedtuple("VariableReference", ["name"])

Call = collections.namedtuple("Call", ["func", "args"])

ReturnStatement = collections.namedtuple("ReturnStatement", ["value"])

FunctionDef = collections.namedtuple("FunctionDef", ["name", "args", "return_annotation", "body"])
Arguments = collections.namedtuple("Arguments", ["args"])
Argument = collections.namedtuple("Argument", ["name", "annotation"])



def none():
    return NoneExpression()


def int(value):
    return IntExpression(value)

str = StringExpression
ref = VariableReference

call = Call

ret = ReturnStatement

func = FunctionDef
arguments = Arguments
argument = Argument


