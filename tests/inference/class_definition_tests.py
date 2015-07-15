from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.identity_dict import NodeDict

from .util import update_context
from ..testing import wip


@istest
def class_type_uses_name_from_node():
    node = nodes.class_("User", [])
    class_type = _infer_class_type(node, [])
    assert_equal("User", class_type.name)
    

@istest
def class_type_has_no_base_classes_if_object_is_explicit_base_class():
    node = nodes.class_("User", [], base_classes=[nodes.ref("object")])
    class_type = _infer_class_type(node, [])
    assert_equal("User", class_type.name)
    assert_equal([], class_type.base_classes)


@istest
def error_if_base_class_is_not_object():
    type_bindings = {"Person": types.meta_type(types.class_type("Person"))}
    node = nodes.class_("User", [], base_classes=[nodes.ref("Person")])
    try:
        _infer_class_type(node, [], type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.UnsupportedError as error:
        assert_equal("base classes other than 'object' are not supported", str(error))


@istest
def class_constructor_takes_no_args_and_returns_class_if_init_not_set():
    node = nodes.class_("User", [])
    meta_type = _infer_meta_type(node, [])
    assert_equal(types.func([], meta_type.type), meta_type.attrs.type_of("__call__"))


@istest
def attributes_defined_in_class_definition_body_are_present_on_class_type():
    node = nodes.class_("User", [
        nodes.assign([nodes.ref("is_person")], nodes.bool_literal(True)),
    ])
    class_type = _infer_class_type(node, ["is_person"])
    assert_equal(types.bool_type, class_type.attrs.type_of("is_person"))


@istest
def attributes_defined_in_class_definition_body_are_present_on_meta_type():
    node = nodes.class_("User", [
        nodes.assign([nodes.ref("is_person")], nodes.bool_literal(True)),
    ])
    meta_type = _infer_meta_type(node, ["is_person"])
    assert_equal(types.bool_type, meta_type.attrs.type_of("is_person"))


@istest
def attributes_with_function_type_defined_in_class_definition_body_are_not_present_on_meta_type():
    node = nodes.class_("User", [
        nodes.assign([nodes.ref("is_person")], nodes.ref("true_func")),
    ])
    meta_type = _infer_meta_type(node, ["is_person"], type_bindings={
        "true_func": types.func([types.object_type], types.none_type)
    })
    assert "is_person" not in meta_type.attrs


@istest
def first_argument_in_method_signature_can_be_strict_supertype_of_class():
    node = nodes.class_("User", [
        nodes.func(
            name="is_person",
            args=nodes.args([nodes.arg("self")]),
            body=[nodes.ret(nodes.bool_literal(True))],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("object"))],
                returns=nodes.ref("bool")
            ),
        )
    ])
    class_type = _infer_class_type(node, ["is_person"])
    assert_equal(types.func([], types.bool_type), class_type.attrs.type_of("is_person"))


@istest
def attributes_with_function_type_defined_in_class_definition_body_are_bound_to_class_type():
    node = nodes.class_("User", [
        nodes.func(
            name="is_person",
            args=nodes.args([nodes.arg("self")]),
            body=[nodes.ret(nodes.bool_literal(True))],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("bool")
            ),
        ),
    ])
    class_type = _infer_class_type(node, ["is_person"])
    assert_equal(types.func([], types.bool_type), class_type.attrs.type_of("is_person"))


@istest
def self_argument_in_method_signature_can_be_explicit_name_of_class():
    node = nodes.class_("User", [
        nodes.func(
            name="is_person",
            args=nodes.args([nodes.arg("self")]),
            body=[nodes.ret(nodes.bool_literal(True))],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("User"))],
                returns=nodes.ref("bool")
            )
        ),
    ])
    class_type = _infer_class_type(node, ["is_person"])
    assert_equal(types.func([], types.bool_type), class_type.attrs.type_of("is_person"))


@istest
def self_argument_in_method_signature_cannot_be_unrelated_type():
    func_node = nodes.func(
        name="is_person",
        args=nodes.args([nodes.arg("self")]),
        body=[nodes.ret(nodes.bool_literal(True))],
        type=nodes.signature(
            args=[nodes.signature_arg(nodes.ref("bool"))],
            returns=nodes.ref("bool")
        ),
    )
    node = nodes.class_("User", [func_node])
    try:
        _infer_class_type(node, ["is_person"])
        assert False, "Expected error"
    except errors.UnexpectedReceiverTypeError as error:
        assert_equal(func_node, error.node)
        assert_equal(types.bool_type, error.receiver_type)
        assert_equal("first argument of methods should have Self type but was 'bool'", str(error))


@istest
def methods_must_have_at_least_one_argument():
    func_node = nodes.func(
        name="is_person",
        args=nodes.args([]),
        body=[nodes.ret(nodes.bool_literal(True))],
        type=nodes.signature(
            args=[],
            returns=nodes.ref("bool")
        )
    )
    node = nodes.class_("User", [func_node])
    try:
        _infer_class_type(node, ["is_person"])
        assert False, "Expected error"
    except errors.MethodHasNoArgumentsError as error:
        assert_equal(func_node, error.node)
        assert_equal("'is_person' method must have at least one argument", str(error))


@istest
def method_signature_is_checked_when_defined_by_assignment():
    func_node = nodes.assign([nodes.ref("is_person")], nodes.ref("f"))
    node = nodes.class_("User", [func_node])
    try:
        _infer_class_type(node, ["is_person"], type_bindings={
            "f": types.func([], types.bool_type)
        })
        assert False, "Expected error"
    except errors.MethodHasNoArgumentsError as error:
        assert_equal(func_node, error.node)
        assert_equal("is_person", error.attr_name)


@wip
@istest
def init_method_is_not_present_on_instance():
    node = _create_class_with_init(
        signature=nodes.signature(
            args=[nodes.signature_arg(nodes.ref("Self"))],
            returns=nodes.ref("none")
        ),
        args=nodes.args([nodes.arg("self")]),
        body=[],
    )
    meta_type = _infer_meta_type(node, ["__init__"])
    assert not "__init__" in meta_type.type.attrs
    

@istest
def init_method_is_used_as_call_method_on_meta_type():
    node = _create_class_with_init(
        signature=nodes.signature(
            args=[nodes.signature_arg(nodes.ref("Self")), nodes.signature_arg(nodes.ref("str"))],
            returns=nodes.ref("none")
        ),
        args=nodes.args([nodes.arg("self"), nodes.arg("name")]),
        body=[],
    )
    meta_type = _infer_meta_type(node, ["__init__"])
    assert_equal(types.func([types.str_type], meta_type.type), meta_type.attrs.type_of("__call__"))
    

@istest
def init_method_must_return_none():
    node = _create_class_with_init(
        signature=nodes.signature(
            args=[nodes.signature_arg(nodes.ref("Self"))],
            returns=nodes.ref("str")
        ),
        args=nodes.args([nodes.arg("self")]),
        body=[nodes.ret(nodes.str_literal(""))],
    )
    try:
        _infer_meta_type(node, ["__init__"])
        assert False, "Expected error"
    except errors.InitMethodsMustReturnNoneError as error:
        assert_equal(node.body[0], error.node)


@istest
def init_must_be_function_definition():
    func_node = nodes.assign([nodes.ref("__init__")], nodes.ref("f"))
    node = nodes.class_("User", [func_node])
    try:
        _infer_class_type(node, ["__init__"], type_bindings={
            "f": types.func([types.object_type], types.str_type)
        })
        assert False, "Expected error"
    except errors.InitAttributeMustBeFunctionDefinitionError as error:
        assert_equal(func_node, error.node)


@istest
def method_can_call_method_on_same_instance_defined_later_in_body():
    node = nodes.class_("User", [
        nodes.func(
            name="f",
            args=nodes.args([nodes.arg("self_f")]),
            body=[
                nodes.ret(nodes.call(nodes.attr(nodes.ref("self_f"), "g"), []))
            ],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("none")
            ),
        ),
        nodes.func(
            name="g",
            args=nodes.args([nodes.arg("self_g")]),
            body=[
                nodes.ret(nodes.call(nodes.attr(nodes.ref("self_g"), "f"), []))
            ],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("none")
            ),
        )
    ])
    _infer_class_type(node, ["f", "g"])


@istest
def init_method_cannot_call_other_methods():
    node = nodes.class_("User", [
        nodes.func(
            name="__init__",
            args=nodes.args([nodes.arg("self_init")]),
            body=[
                nodes.assign([nodes.ref("x")], nodes.call(nodes.attr(nodes.ref("self_init"), "g"), []))
            ],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("none")
            ),
        ),
        nodes.func(
            name="g",
            args=nodes.args([nodes.arg("self_g")]),
            body=[],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("none")
            ),
        ),
    ])
    try:
        _infer_class_type(node, ["__init__", "g"])
        assert False, "Expected error"
    except errors.InitMethodCannotGetSelfAttributes as error:
        assert_equal("__init__ methods cannot get attributes of self", str(error))


@istest
def attributes_assigned_with_explicit_type_in_init_can_be_used_in_methods():
    init_func = nodes.func(
        name="__init__",
        args=nodes.args([nodes.arg("self_init")]),
        body=[
            nodes.assign(
                [nodes.attr(nodes.ref("self_init"), "message")],
                nodes.str_literal("Hello"),
                type=nodes.ref("str"),
            )
        ],
        type=nodes.signature(
            args=[nodes.signature_arg(nodes.ref("Self"))],
            returns=nodes.ref("none")
        ),
    )
    node = nodes.class_("User", [
        init_func,
        nodes.func(
            name="g",
            args=nodes.args([nodes.arg("self_g")]),
            body=[nodes.ret(nodes.attr(nodes.ref("self_g"), "message"))],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("str")
            ),
        )
    ])
    _infer_class_type(node, ["__init__", "g"], [(init_func, ["self_init"])])


@istest
def attributes_assigned_in_init_can_be_used_in_methods_when_init_method_is_defined_after_other_method():
    init_func = nodes.func(
        name="__init__",
        args=nodes.args([nodes.arg("self_init")]),
        body=[
            nodes.assign(
                [nodes.attr(nodes.ref("self_init"), "message")],
                nodes.str_literal("Hello"),
                type=nodes.ref("str"),
            )
        ],
        type=nodes.signature(
            args=[nodes.signature_arg(nodes.ref("Self"))],
            returns=nodes.ref("none")
        ),
    )
    node = nodes.class_("User", [
        nodes.func(
            name="g",
            args=nodes.args([nodes.arg("self_g")]),
            body=[nodes.ret(nodes.attr(nodes.ref("self_g"), "message"))],
            type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))],
                returns=nodes.ref("str")
            ),
        ),
        init_func,
    ])
    _infer_class_type(node, ["__init__", "g"], [(init_func, ["self_init"])])

@istest
def name_of_instantiation_of_generic_class_includes_type_parameters():
    node = nodes.class_("Option", [], type_params=[nodes.formal_type_parameter("T")])
    class_type = _infer_class_type(node, [])
    assert_equal("Option[int]", class_type(types.int_type).name)


def _create_class_with_init(signature, args, body):
    return nodes.class_("User", [
        nodes.func(
            name="__init__",
            args=args,
            body=body,
            type=signature
        )
    ])
    


def _infer_meta_type(class_node, names, names_in_nodes=None, type_bindings=None):
    if type_bindings is None:
        type_bindings = {}
    else:
        type_bindings = type_bindings.copy()
    if names_in_nodes is None:
        names_in_nodes = []
    
    type_bindings["bool"] = types.meta_type(types.bool_type)
    type_bindings["object"] = types.meta_type(types.object_type)
    type_bindings["none"] = types.meta_type(types.none_type)
    type_bindings["str"] = types.meta_type(types.str_type)
    context = update_context(
        class_node,
        declared_names_in_node=NodeDict(names_in_nodes + [(class_node, names + ["Self"])]),
        type_bindings=type_bindings,
    )
    meta_type = context.lookup(class_node)
    assert isinstance(meta_type, types.MetaType)
    assert types.is_class_type(meta_type.type) or types.is_generic_type(meta_type.type)
    return meta_type


def _infer_class_type(class_node, names, names_in_nodes=None, type_bindings=None):
    return _infer_meta_type(class_node, names, names_in_nodes, type_bindings=type_bindings).type
    
