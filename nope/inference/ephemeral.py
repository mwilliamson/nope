import collections

from .. import nodes


def attr(value, attr):
    return EphemeralNode(value, nodes.attr(value, attr))


def call(root_node, receiver, args):
    return EphemeralNode(root_node, nodes.call(receiver, args))


class EphemeralNode(object):
    def __init__(self, root_node, node):
        self._root_node = root_node
        self._node = node
    
    def __getattr__(self, name):
        return getattr(self._node, name)
    
    def __eq__(self, other):
        if not isinstance(other, EphemeralNode):
            return False
        
        return (self._root_node, self._node) == (other._root_node, other._node)
    
    def __neq__(self, other):
        return not (self == other)


def root_node(node):
    while isinstance(node, EphemeralNode):
        node = node._root_node
        
    return node


def underlying_node(node):
    return node._node


def formal_arg_constraint(formal_arg_node, type_=None):
    if type_ is None:
        type_ = formal_arg_node
        formal_arg_node = None
    return FormalArgumentConstraint(formal_arg_node, type_)


class FormalArgumentConstraint(object):
    def __init__(self, formal_arg_node, type_):
        self.formal_arg_node = formal_arg_node
        self.type = type_


def formal_arg(func, index):
    return EphemeralNode(func, FormalArg(func, index))
    

FormalArg = collections.namedtuple("FormalArg", ["func", "index"])
