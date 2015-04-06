from nose.tools import assert_equal

from nope import types, errors, nodes, inference, name_declaration, modules
from nope.inference.context import Context
from nope.modules import LocalModule
from nope.module_resolution import ResolvedImport
from nope.identity_dict import NodeDict


def update_context(statement, *, type_bindings=None, module_resolver=None, module_types=None, module_path=None, is_executable=False, declared_names_in_node=None, update_deferred=True):
    if type_bindings is None:
        type_bindings = {}
    declaration_finder, context = _create_context(type_bindings, declared_names_in_node)
    checker = _create_type_checker(
        declaration_finder=declaration_finder,
        module_path=module_path,
        module_resolver=module_resolver,
        module_types=module_types,
        is_executable=is_executable,
    )
    checker.update_context(statement, context)
    if update_deferred:
        context.update_deferred()
    return context


def infer(expression, type_bindings=None, hint=None):
    if type_bindings is None:
        type_bindings = {}
    
    declaration_finder, context = _create_context(type_bindings)
    checker = _create_type_checker(declaration_finder=declaration_finder)
    return checker.infer(expression, context, hint=hint)
    

def _create_type_checker(declaration_finder=None, module_types=None, module_resolver=None, module_path=None, is_executable=False):
    return inference._TypeCheckerForModule(
        declaration_finder=declaration_finder,
        name_resolver=None,
        module_exports=modules.ModuleExports(declaration_finder),
        module_resolver=module_resolver,
        module_types=module_types,
        module=LocalModule(module_path, nodes.module([], is_executable=is_executable)),
    )


class SingleScopeReferences(object):
    def __init__(self, names=None, references=None):
        if names is None:
            names = []
        if references is None:
            references = {}
        
        self._names = names
        self._references = references
    
    def referenced_declaration(self, node):
        named_nodes = (
            nodes.VariableReference,
            nodes.Argument,
            nodes.FunctionDef,
            nodes.ClassDefinition,
            nodes.TypeDefinition,
            nodes.FormalTypeParameter,
        )
        if isinstance(node, named_nodes):
            name = node.name
        elif isinstance(node, nodes.ImportAlias):
            name = node.value_name
        else:
            raise Exception("Name not implemented for {}".format(type(node)))
        
        return self.declaration(name)
    
    def declaration(self, name):
        if name not in self._references:
            self._references[name] = name_declaration.VariableDeclarationNode(name)
        
        return self._references[name]
    
    def names(self):
        return self._names
    
    def with_names(self, names):
        return SingleScopeReferences(names, self._references)


class FakeDeclarationFinder(object):
    def __init__(self, references, declared_names_in_node):
        self._references = references
        self._declared_names_in_node = declared_names_in_node
    
    def declarations_in(self, node):
        names = self._declared_names_in_node.get(node, [])
        return self._references.with_names(names)


def _create_context(types=None, declared_names_in_node=None):
    if types is None:
        types = {}
    
    references = SingleScopeReferences()
    context = SingleScopeContext(references)
    declaration_finder = FakeDeclarationFinder(references, declared_names_in_node)
    
    for name, type_ in types.items():
        context.update_type(nodes.ref(name), type_)
    
    return declaration_finder, context


class SingleScopeContext(object):
    def __init__(self, references):
        self._context = Context(references, {}, NodeDict())
    
    def __getattr__(self, key):
        return getattr(self._context, key)
    
    def lookup_name(self, name):
        return self.lookup(nodes.ref(name))
    


def update_blank_context(node, *args, **kwargs):
    return update_context(node, *args, **kwargs)


def module(attrs):
    return types.module("generic_module_name", attrs)


class FakeModuleTypes(object):
    def __init__(self, modules):
        self._modules = modules
    
    def type_of_module(self, path):
        return self._modules.get(path)


class FakeModuleResolver(object):
    def __init__(self, modules):
        self._modules = modules
    
    def resolve_import_value(self, names, value_name):
        # TODO: this resembles an actual implementation too much for a stub
        if tuple(names) in self._modules:
            return ResolvedImport(names, self.resolve_import_path(names), value_name)
        else:
            module_name = names + [value_name]
            return ResolvedImport(module_name, self.resolve_import_path(module_name), None)
    
    def resolve_import_path(self, names):
        try:
            return self._modules[tuple(names)]
        except KeyError:
            raise errors.ModuleNotFoundError(None, str(names))


def assert_type_mismatch(func, expected, actual, node):
    try:
        func()
        assert False, "Expected type mismatch"
    except errors.UnexpectedValueTypeError as mismatch:
        assert_equal(expected, mismatch.expected)
        assert_equal(actual, mismatch.actual)
        assert mismatch.node is node


def assert_statement_type_checks(statement, type_bindings):
    update_context(statement, type_bindings=type_bindings)


def assert_statement_is_type_checked(create_node, type_bindings=None):
    assert_expression_is_type_checked(
        lambda bad_expression: create_node(nodes.expression_statement(bad_expression)),
        type_bindings=type_bindings,
    )


def assert_expression_is_type_checked(create_node, type_bindings=None):
    if type_bindings is None:
        type_bindings = {}
    
    bad_ref = nodes.ref("bad")
    node = create_node(bad_ref)
    
    try:
        update_context(node, type_bindings=type_bindings)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(bad_ref, error.node)
        assert_equal("bad", error.name)


def assert_subexpression_is_type_checked(create_node):
    bad_ref = nodes.ref("bad")
    node = create_node(bad_ref)
    
    try:
        infer(node, {})
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(bad_ref, error.node)
        assert_equal("bad", error.name)



def context_manager_class(enter_type=None, exit_type=None):
    return types.class_type("Manager", [
        types.attr("__enter__", enter_method(enter_type), read_only=True),
        types.attr("__exit__", exit_method(exit_type), read_only=True),
    ])


def enter_method(return_type=None):
    if return_type is None:
        return_type = types.none_type
    return types.func([], return_type)


def exit_method(return_type=None):
    if return_type is None:
        return_type = types.none_type
    
    return types.func(
        [
            types.union(types.exception_meta_type, types.none_type),
            types.union(types.exception_type, types.none_type),
            types.union(types.traceback_type, types.none_type)
        ],
        return_type
    )
