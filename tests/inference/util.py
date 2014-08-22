from nose.tools import assert_equal

from nope import types, errors, nodes
from nope.context import bound_context
from nope.inference import update_context


def update_blank_context(node, *args, declared_names=[], **kwargs):
    context = bound_context(dict((name, None) for name in declared_names))
    update_context(node, context, *args, **kwargs)
    return context


def module(attrs):
    return types.module("generic_module_name", attrs)


class FakeSourceTree(object):
    def __init__(self, modules):
        self._modules = modules
    
    def import_module(self, path):
        return self._modules.get(path)
    
    def __contains__(self, value):
        return value in self._modules


def assert_type_mismatch(func, expected, actual, node):
    try:
        func()
        assert False, "Expected type mismatch"
    except errors.TypeMismatchError as mismatch:
        assert_equal(expected, mismatch.expected)
        assert_equal(actual, mismatch.actual)
        assert mismatch.node is node



def assert_variable_remains_unbound(create_node):
    assignment = nodes.assign("x", nodes.int(1))
    node = create_node(assignment)
    context = bound_context({"x": None})
    update_context(node, context)
    assert not context.is_bound("x")
    assert_equal(types.int_type, context.lookup("x", allow_unbound=True))


def assert_statement_type_checks(statement, context):
    update_context(statement, context)


def assert_statement_is_type_checked(create_node, context=None):
    assert_expression_is_type_checked(
        lambda bad_expression: create_node(nodes.expression_statement(bad_expression)),
        context
    )


def assert_expression_is_type_checked(create_node, context=None):
    if context is None:
        context = bound_context({})
    
    bad_ref = nodes.ref("bad")
    node = create_node(bad_ref)
    
    try:
        update_context(node, context)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(bad_ref, error.node)
        assert_equal("bad", error.name)


def assert_variable_is_bound(create_node):
    assignment = nodes.assign("x", nodes.int(1))
    node = create_node(assignment)
    context = bound_context({"x": None})
    update_context(node, context)
    assert context.is_bound("x")
    assert_equal(types.int_type, context.lookup("x"))
