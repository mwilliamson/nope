import ast
import collections


NoneExpression = collections.namedtuple("NoneExpression", [])
IntExpression = collections.namedtuple("IntExpression", ["value"])
StringExpression = collections.namedtuple("StringExpression", ["value"])
VariableReference = collections.namedtuple("VariableReference", ["name"])

ReturnStatement = collections.namedtuple("ReturnStatement", ["value"])

FunctionDef = collections.namedtuple("FunctionDef", ["args", "return_annotation", "body"])
Arguments = collections.namedtuple("Arguments", ["args"])
Argument = collections.namedtuple("Argument", ["name", "annotation"])



def none():
    return NoneExpression()


def int(value):
    return IntExpression(value)

str = StringExpression
func = FunctionDef
arguments = Arguments
argument = Argument
ref = VariableReference
ret = ReturnStatement
