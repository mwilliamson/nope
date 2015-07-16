from .. import nodes

def is_literal(node):
    if isinstance(node, (nodes.NoneLiteral, nodes.BooleanLiteral, nodes.StringLiteral, nodes.IntLiteral)):
        return True
    if isinstance(node, (nodes.ListLiteral, nodes.TupleLiteral)):
        return all(map(is_literal, node.elements))
    if isinstance(node, (nodes.DictLiteral)):
        return all(
            is_literal(key) and is_literal(value)
            for key, value in node.items
        )
    return False
