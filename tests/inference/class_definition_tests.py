from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.context import Context
from nope.identity_dict import IdentityDict

from .util import assert_type_mismatch, update_context, SingleScopeReferences


@istest
def class_type_uses_name_from_node():
    node = nodes.class_def("User", [])
    class_type = _infer_class_type(node, [])
    assert_equal("User", class_type.name)


@istest
def class_constructor_takes_no_args_and_returns_class_if_init_not_set():
    node = nodes.class_def("User", [])
    meta_type = _infer_meta_type(node, [])
    assert_equal(types.func([], meta_type.type), meta_type.attrs.type_of("__call__"))


@istest
def attributes_defined_in_class_definition_body_are_present_on_class_type():
    node = nodes.class_def("User", [
        nodes.assign([nodes.ref("is_person")], nodes.boolean(True)),
    ])
    class_type = _infer_class_type(node, ["is_person"])
    assert_equal(types.boolean_type, class_type.attrs.type_of("is_person"))


@istest
def attributes_defined_in_class_definition_body_are_present_on_meta_type():
    node = nodes.class_def("User", [
        nodes.assign([nodes.ref("is_person")], nodes.boolean(True)),
    ])
    meta_type = _infer_meta_type(node, ["is_person"])
    assert_equal(types.boolean_type, meta_type.attrs.type_of("is_person"))
    


def _infer_meta_type(class_node, names):
    context = update_context(class_node, declared_names_in_node=IdentityDict([(class_node, names)]))
    meta_type = context.lookup(class_node)
    assert isinstance(meta_type, types.MetaType)
    assert isinstance(meta_type.type, types._ScalarType)
    return meta_type


def _infer_class_type(class_node, names):
    return _infer_meta_type(class_node, names).type
    
