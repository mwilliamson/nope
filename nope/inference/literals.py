from .. import nodes

def is_literal(node):
    if isinstance(node, (nodes.NoneLiteral, nodes.StringLiteral, nodes.IntLiteral)):
        return True
    if isinstance(node, (nodes.ListLiteral, nodes.TupleLiteral)):
        return all(map(is_literal, node.elements))
    return False
