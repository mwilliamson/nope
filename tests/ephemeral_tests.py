from nose.tools import istest, assert_is

from nope.inference import ephemeral
from nope import nodes


@istest
def test_root_node_of_ephemeral_attr_is_left_value_if_left_value_is_not_ephemeral():
    ref_node = nodes.ref("x")
    assert_is(ref_node, ephemeral.root_node(ephemeral.attr(ref_node, "__len__")))


@istest
def test_root_node_of_ephemeral_node_recurses_up_tree_until_non_ephemeral_node():
    ref_node = nodes.ref("x")
    node = ephemeral.attr(ephemeral.attr(ref_node, "__call__"), "__call__")
    assert_is(ref_node, ephemeral.root_node(node))
