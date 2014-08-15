from .. import nodes


def attr(value, attr):
    return EphemeralNode(nodes.attr(value, attr))


class EphemeralNode(object):
    def __init__(self, node):
        self._node = node
    
    def __getattr__(self, name):
        return getattr(self._node, name)
