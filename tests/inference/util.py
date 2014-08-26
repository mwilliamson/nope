from nose.tools import assert_equal

from nope import types, errors, nodes, inference, name_declaration
from nope.context import Context


def update_context(statement, context=None, source_tree=None, module_path=None, is_executable=False):
    if context is None:
        context = create_context()
    checker = _create_type_checker(module_path=module_path, source_tree=source_tree, is_executable=is_executable)
    checker.update_context(statement, context)
    
    return context


def infer(expression, context=None):
    if context is None:
        context = create_context()
    
    checker = _create_type_checker()
    return checker.infer(expression, context)
    

def _create_type_checker(source_tree=None, module_path=None, is_executable=False):
    return inference._TypeChecker(
        source_tree=source_tree,
        module_path=module_path,
        is_executable=is_executable,
    )


class SingleScopeReferences(object):
    def __init__(self):
        self._references = {}
    
    def resolve(self, node):
        if isinstance(node, (nodes.VariableReference, nodes.Argument, nodes.FunctionDef)):
            name = node.name
        elif isinstance(node, nodes.ImportAlias):
            name = node.value_name
        else:
            raise Exception("Name not implemented for {}".format(type(node)))
        
        if name not in self._references:
            self._references[name] = name_declaration.VariableDeclarationNode(name)
        
        return self._references[name]


def create_context(types=None):
    if types is None:
        types = {}
        
    context = SingleScopeContext()
    
    for name, type_ in types.items():
        context.update_type(nodes.ref(name), type_)
    
    return context


class SingleScopeContext(object):
    def __init__(self):
        self._context = Context(SingleScopeReferences(), {})
    
    def __getattr__(self, key):
        return getattr(self._context, key)
    
    def lookup_name(self, name):
        return self.lookup(nodes.ref(name))
    


def update_blank_context(node, *args, **kwargs):
    context = create_context()
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
        context = create_context()
    
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
