import io

import dodge

from .. import oo
from ..oo import (
    Statements, statements,
    
    ExpressionStatement, expression_statement,
    ReturnStatement, ret,
    AssignmentExpression, assignment_expression as assign,
    
    Call, call,
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

declare = VariableDeclaration = dodge.data_class("VariableDeclaration", ["name"])

lambda_ = LambdaExpression = dodge.data_class("LambdaExpression", ["args", "body"])
arg = Argument = dodge.data_class("Argument", ["name"])

type_apply = TypeApplication = dodge.data_class("TypeApplication", ["func", "args"])
cast = Cast = dodge.data_class("Cast", ["type", "value"])

dynamic = ref("dynamic")
null = ref("null")


def _serialize_variable_declaration(node, writer):
    writer.write("dynamic ")
    writer.write(node.name)
    writer.end_simple_statement()


def _serialize_lambda(node, writer):
    writer.write("((")
    
    for index, arg in enumerate(node.args):
        if index > 0:
            writer.write(", ")
        writer.write("dynamic ")
        writer.write(arg.name)
    
    writer.write(") =>")
    writer.newline()
    writer.start_block()
    for child in node.body:
        writer.dump(child)
    writer.end_block()
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
    VariableDeclaration: _serialize_variable_declaration,

    LambdaExpression: _serialize_lambda,

    Cast: _serialize_cast,
    TypeApplication: _serialize_type_application,
})
