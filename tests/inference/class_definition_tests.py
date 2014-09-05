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


@istest
def attributes_with_function_type_defined_in_class_definition_body_are_not_present_on_meta_type():
    node = nodes.class_def("User", [
        nodes.assign([nodes.ref("is_person")], nodes.ref("true_func")),
    ])
    meta_type = _infer_meta_type(node, ["is_person"], type_bindings={
        "true_func": types.func([types.object_type], types.none_type)
    })
    assert "is_person" not in meta_type.attrs


@istest
def first_argument_in_method_signature_can_be_strict_supertype_of_class():
    node = nodes.class_def("User", [
        nodes.func(
            name="is_person",
            signature=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("object"))],
                returns=nodes.ref("bool")
            ),
            args=nodes.args([nodes.arg("self")]),
            body=[nodes.ret(nodes.boolean(True))],
        )
    ])
    class_type = _infer_class_type(node, ["is_person"])
    assert_equal(types.func([], types.boolean_type), class_type.attrs.type_of("is_person"))


@istest
def attributes_with_function_type_defined_in_class_definition_body_are_bound_to_class_type():
    node = nodes.class_def("User", [
        nodes.func(
            name="is_person",
            signature=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("bool")
            ),
            args=nodes.args([nodes.arg("self")]),
            body=[nodes.ret(nodes.boolean(True))],
        )
    ])
    class_type = _infer_class_type(node, ["is_person"])
    assert_equal(types.func([], types.boolean_type), class_type.attrs.type_of("is_person"))


@istest
def self_argument_in_method_signature_cannot_be_unrelated_type():
    signature_arg_type_node = nodes.ref("bool")
    func_node = nodes.func(
        name="is_person",
        signature=nodes.signature(
            args=[nodes.signature_arg(signature_arg_type_node)],
            returns=nodes.ref("bool")
        ),
        args=nodes.args([nodes.arg("self")]),
        body=[nodes.ret(nodes.boolean(True))],
    )
    node = nodes.class_def("User", [func_node])
    try:
        _infer_class_type(node, ["is_person"])
        assert False, "Expected error"
    except errors.UnexpectedTargetTypeError as error:
        assert_equal(signature_arg_type_node, error.node)
        assert_equal(types.boolean_type, error.target_type)
        assert_equal("User", error.value_type.name)


@istest
def methods_must_have_at_least_one_argument():
    func_node = nodes.func(
        name="is_person",
        signature=nodes.signature(
            args=[],
            returns=nodes.ref("bool")
        ),
        args=nodes.args([]),
        body=[nodes.ret(nodes.boolean(True))],
    )
    node = nodes.class_def("User", [func_node])
    try:
        _infer_class_type(node, ["is_person"])
        assert False, "Expected error"
    except errors.MethodHasNoArgumentsError as error:
        assert_equal(func_node, error.node)
        assert_equal("methods must have at least one argument", str(error))


def _infer_meta_type(class_node, names, type_bindings=None):
    if type_bindings is None:
        type_bindings = {}
    else:
        type_bindings = type_bindings.copy()
    
    type_bindings["bool"] = types.meta_type(types.boolean_type)
    type_bindings["object"] = types.meta_type(types.object_type)
    context = update_context(
        class_node,
        declared_names_in_node=IdentityDict([(class_node, names + ["Self"])]),
        type_bindings=type_bindings,
    )
    meta_type = context.lookup(class_node)
    assert isinstance(meta_type, types.MetaType)
    assert isinstance(meta_type.type, types._ScalarType)
    return meta_type


def _infer_class_type(class_node, names):
    return _infer_meta_type(class_node, names).type
    
