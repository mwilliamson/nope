from nose.tools import istest, assert_equal

from nope import types, nodes, errors

from .util import assert_statement_type_checks, update_context


@istest
def raise_value_can_be_instance_of_exception():
    type_bindings = {"error": types.exception_type}
    assert_statement_type_checks(nodes.raise_statement(nodes.ref("error")), type_bindings=type_bindings)


@istest
def raise_value_can_be_instance_of_subtype_of_exception():
    cls = types.scalar_type("BlahError", {}, base_classes=[types.exception_type])
    type_bindings = {"error": cls}
    assert_statement_type_checks(nodes.raise_statement(nodes.ref("error")), type_bindings=type_bindings)


@istest
def raise_value_cannot_be_non_subtype_of_exception():
    type_bindings = {"error": types.object_type}
    ref_node = nodes.ref("error")
    try:
        update_context(nodes.raise_statement(ref_node), type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(ref_node, error.node)
