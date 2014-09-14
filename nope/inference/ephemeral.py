import dodge

from .. import nodes


def attr(value, attr):
    return _ephemeral(value, nodes.attr(value, attr))


def call(root_node, receiver, args):
    return _ephemeral(root_node, nodes.call(receiver, args))


def _ephemeral(root_node, node):
    node._ephemeral_root_node = root_node
    return node


def _is_ephemeral(node):
    return hasattr(node, "_ephemeral_root_node")


def root_node(node):
    while _is_ephemeral(node):
        node = node._ephemeral_root_node
        
    return node


def underlying_node(node):
    return node


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
    return _ephemeral(func, FormalArg(func, index))
    

FormalArg = dodge.data_class("FormalArg", ["func", "index"])
