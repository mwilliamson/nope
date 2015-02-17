import dodge

from .. import oo
from ..oo import (
    Statements, statements,
    
    ExpressionStatement, expression_statement,
    
    Call, call,
    VariableReference, ref,
    IntegerLiteral, integer_literal,
)


def dump(node, fileobj):
    writer = oo.Writer(_serializers, fileobj)
    return writer.dump(node)


_serializers = oo.serializers({})
