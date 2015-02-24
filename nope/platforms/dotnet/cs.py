import io
import functools

import dodge

from .. import oo
from ..oo import (
    Statements, statements,
    
    IfElse, if_,
    WhileLoop, while_,
    break_,
    continue_,
    
    Throw,
    
    ExpressionStatement, expression_statement,
    ReturnStatement, ret,
    AssignmentExpression, assignment_expression as assign,
    
    UnaryOperation, unary_operation,
    TernaryConditional, ternary_conditional,
    Call, call,
    PropertyAccess, property_access,
    VariableReference, ref,
    String as StringLiteral, string as string_literal,
    IntegerLiteral, integer_literal,
)


def dump(node, fileobj):
    writer = oo.Writer(_serializers, fileobj)
    return writer.dump(node)


def dumps(node):
    output = io.StringIO()
    dump(node, output)
    return output.getvalue()


class_ = ClassDefinition = dodge.data_class("ClassDefinition", ["name", "members"])
method = Method = dodge.data_class("Method", ["name", "args", "body"])

TryStatement = dodge.data_class("TryStatement", ["try_body", "handlers", "finally_body"])

def try_(try_body, handlers=None, finally_body=None):
    if handlers is None:
        handlers = []
    if finally_body is None:
        finally_body = []
    return TryStatement(try_body, handlers, finally_body)


catch = CatchStatement = dodge.data_class("CatchStatement", ["type", "name", "body"])

def throw(value=None):
    return Throw(value)

declare = VariableDeclaration = dodge.data_class("VariableDeclaration", ["name", "value"])

def new(constructor, args, members=None):
    if members is None:
        members = []
    
    return New(constructor, args, members)

New = dodge.data_class("New", ["constructor", "args", "members"])
obj = ObjectLiteral = dodge.data_class("ObjectLiteral", ["members"])
lambda_ = LambdaExpression = dodge.data_class("LambdaExpression", ["args", "body"])
arg = Argument = dodge.data_class("Argument", ["name"])

type_apply = TypeApplication = dodge.data_class("TypeApplication", ["func", "args"])
cast = Cast = dodge.data_class("Cast", ["type", "value"])

dynamic = ref("dynamic")
null = ref("null")
not_ = functools.partial(unary_operation, "!")
break_ = break_()
continue_ = continue_()
this = ref("this")


def _serialize_class_definition(node, writer):
    writer.write("internal class ")
    writer.write(node.name)
    writer.write(" ")
    writer.start_block()
    
    for name in node.members:
        writer.write("internal dynamic ")
        writer.write(name)
        writer.write(";")
        writer.newline()
    
    writer.end_block()


def _serialize_method(node, writer):
    writer.write("internal dynamic ")
    writer.write(node.name)
    
    _serialize_formal_args(node.args, writer)
    writer.write(" ")
    
    writer.dump_block(node.body)
    writer.end_compound_statement()


def _serialize_try_statement(node, writer):
    writer.write("try ")
    writer.dump_block(node.try_body)
    
    for handler in node.handlers:
        writer.dump(handler)
    
    if node.finally_body:
        writer.write(" finally ")
        writer.dump_block(node.finally_body)
    
    writer.end_compound_statement()


def _serialize_catch(node, writer):
    writer.write(" catch ")
    
    if node.type is not None:
        writer.write("(")
        writer.dump(node.type)
    
        if node.name is not None:
            writer.write(" ")
            writer.write(node.name)
        
        writer.write(") ")
    
    writer.dump_block(node.body)


def _serialize_variable_declaration(node, writer):
    writer.write("dynamic ")
    writer.write(node.name)
    if node.value is not None:
        writer.write(" = ")
        writer.dump(node.value)
    writer.end_simple_statement()


def _serialize_new(node, writer):
    writer.write("new ")
    writer.dump(node.constructor)
    
    if not node.members or node.args:
        writer.write("(")
        
        for index, arg in enumerate(node.args):
            if index > 0:
                writer.write(", ")
            writer.dump(arg)
        
        writer.write(")")
    
    if node.members:
        writer.write(" ")
        writer.start_block()
        for name, value in node.members:
            writer.write(name)
            writer.write(" = ")
            writer.dump(value)
            writer.write(",")
            writer.newline()
        writer.end_block()


def _serialize_object(node, writer):
    writer.write("new")
    writer.newline()
    writer.start_block()
    
    for key, value in node.members:
        writer.write(key)
        writer.write(" = ")
        writer.dump(value)
        writer.write(",")
        writer.newline()
    
    writer.end_block()


def _serialize_lambda(node, writer):
    writer.write("(")
    _serialize_formal_args(node.args, writer)
    writer.write(" =>")
    writer.newline()
    writer.dump_block(node.body)
    writer.write(")")


def _serialize_formal_args(args, writer):
    writer.write("(")
    for index, arg in enumerate(args):
        if index > 0:
            writer.write(", ")
        writer.write("dynamic ")
        writer.write(arg.name)
    writer.write(")")


def _serialize_cast(cast, writer):
    writer.write("(")
    
    writer.write("(")
    writer.dump(cast.type)
    writer.write(")")
    writer.dump(cast.value)
    
    writer.write(")")


def _serialize_type_application(node, writer):
    writer.dump(node.func)
    writer.write("<")
    
    for index, arg in enumerate(node.args):
        if index > 0:
            writer.write(", ")
        writer.dump(arg)
    
    writer.write(">")


_serializers = oo.serializers({
    ClassDefinition: _serialize_class_definition,
    Method: _serialize_method,

    TryStatement: _serialize_try_statement,
    CatchStatement: _serialize_catch,
    VariableDeclaration: _serialize_variable_declaration,

    New: _serialize_new,
    ObjectLiteral: _serialize_object,
    LambdaExpression: _serialize_lambda,

    Cast: _serialize_cast,
    TypeApplication: _serialize_type_application,
})
