from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.context import Context

from .util import assert_type_mismatch, update_context, SingleScopeReferences


@istest
def empty_class_definition_updates_type_to_meta_class_of_scalar_class():
    node = nodes.class_def("User", [])
    meta_type = _infer_class_type(node)
    assert isinstance(meta_type, types.MetaType)
    class_type = meta_type.type
    assert isinstance(class_type, types._ScalarType)
    assert_equal("User", class_type.name)
    assert_equal(types.func([], class_type), meta_type.attrs.type_of("__call__"))
    


def _infer_class_type(class_node):
    context = Context(SingleScopeReferences(), {}).enter_module()
    update_context(class_node, context)
    return context.lookup(class_node)
