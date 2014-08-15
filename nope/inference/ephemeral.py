from .. import nodes


def attr(value, attr):
    return EphemeralNode(value, nodes.attr(value, attr))


class EphemeralNode(object):
    def __init__(self, root_node, node):
        self._root_node = root_node
        self._node = node
    
    def __getattr__(self, name):
        return getattr(self._node, name)


def root_node(node):
    # TODO: should keep recursing until we reach a non-ephemeral node
    return node._root_node


def underlying_node(node):
    return node._node
