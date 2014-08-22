from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.inference import update_context
from nope.context import bound_context

from .util import assert_statement_type_checks


@istest
def raise_value_can_be_instance_of_exception():
    context = bound_context({"error": types.exception_type})
    assert_statement_type_checks(nodes.raise_statement(nodes.ref("error")), context)


@istest
def raise_value_can_be_instance_of_subtype_of_exception():
    cls = types.scalar_type("BlahError", {}, base_classes=[types.exception_type])
    context = bound_context({"error": cls})
    assert_statement_type_checks(nodes.raise_statement(nodes.ref("error")), context)


@istest
def raise_value_cannot_be_non_subtype_of_exception():
    context = bound_context({"error": types.object_type})
    ref_node = nodes.ref("error")
    try:
        update_context(nodes.raise_statement(ref_node), context)
        assert False, "Expected error"
    except errors.TypeMismatchError as error:
        assert_equal(ref_node, error.node)
