from . import nodes, errors, structure, name_declaration, types
from .lists import filter_by_type
from .dispatch import TypeDispatch


def check_bindings(node, references, type_lookup, is_definitely_bound):
    context = _Context(references, is_definitely_bound, {})
    checker = _BindingChecker(type_lookup)
    checker.process_bindings(node, context)
    context.update_deferred()
    return Bindings(references, context._is_definitely_bound)


class _BindingChecker(object):
    _binding_nodes = set([
        nodes.Argument,
        nodes.ImportAlias,
        nodes.TypeDefinition,
        nodes.StructuralTypeDefinition,
    ])
    
    def __init__(self, type_lookup):
        self._type_lookup = type_lookup
        self._update_bindings = TypeDispatch({
            structure.Branch: self._update_branch_node,
            structure.ExhaustiveBranches: self._update_exhaustive_branches,
            structure.Delete: self._update_delete,
            nodes.Target: self._update_target_node,
            nodes.FunctionDef: self._update_function_definition,
            nodes.ClassDefinition: self._update_class_definition,
        }, default=self._update_children)
    
    def process_bindings(self, node, context):
        if isinstance(node, nodes.VariableReference):
            self._check_variable_reference(node, context)
        
        self._update_bindings(node, context)
        
        if type(node) in self._binding_nodes:
            context.bind(node)


    def _update_children(self, node, context):
        for child in structure.children(node, self._type_lookup):
            self.process_bindings(child, context)


    def _check_variable_reference(self, node, context):
        if not context.is_definitely_bound(node):
            raise errors.UnboundLocalError(node, node.name)
    
    
    def _update_branch_node(self, node, context):
        branch_context = self._update_branched_nodes(node.body, context)
        context.after_branch(branch_context)
        
    
    def _update_branched_nodes(self, nodes, context):
        branch_context = context.enter_branch()
        self._update_statements(nodes, branch_context)
        return branch_context

    def _update_exhaustive_branches(self, node, context):
        branch_contexts = [
            self._update_branched_nodes(branch, context)
            for branch in node.branches
        ]
        context.unify(branch_contexts)

    def _update_delete(self, node, context):
        assert isinstance(node.target, nodes.VariableReference)
        
        context.delete(node.target)

    def _update_target(self, target, context):
        if isinstance(target, nodes.TupleLiteral):
            for element in target.elements:
                self._update_target(element, context)
        else:
            if isinstance(target, nodes.VariableReference):
                context.bind(target)
            self.process_bindings(target, context)
    
    
    def _update_target_node(self, node, context):
        self._update_target(node.value, context)


    def _update_function_definition(self, node, context):
        context.bind(node)
        context.add_deferred(node, lambda: self._update_function_definition_body(node, context))
        
    
    def _update_function_definition_body(self, node, context):
        body_context = context.enter_new_namespace()
        self.process_bindings(node.args, body_context)
        self._update_statements(node.body, body_context)


    def _update_class_definition(self, node, context):
        body_context = context.enter_new_namespace()
        self._update_statements(node.body, body_context)
        context.add_deferred(node, lambda: self._update_class_on_reference(node, context))
    
    def _update_class_on_reference(self, node, context):
        context.bind(node)
        methods = filter_by_type(nodes.FunctionDef, node.body)
        for method in methods:
            context.is_definitely_bound(method)
    
    
    def _update_statements(self, statements, context):
        for statement in statements:
            self.process_bindings(statement, context)



class _Context(object):
    def __init__(self, references, is_definitely_bound, deferred):
        self._references = references
        self._is_definitely_bound = is_definitely_bound
        self._deferred = deferred
    
    def is_definitely_bound(self, node):
        declaration = self._references.referenced_declaration(node)
        return self.is_declaration_definitely_bound(declaration)
    
    def is_declaration_definitely_bound(self, declaration):
        if declaration in self._deferred:
            self._deferred.pop(declaration)()
            
        return self._is_definitely_bound.get(declaration, False)
    
    def bind(self, node):
        declaration = self._references.referenced_declaration(node)
        self._is_definitely_bound[declaration] = True
    
    
    def delete(self, node):
        declaration = self._references.referenced_declaration(node)
        self._is_definitely_bound[declaration] = False
    
    def enter_branch(self):
        return _Context(self._references, DiffingDict(self._is_definitely_bound), self._deferred)
    
    def enter_new_namespace(self):
        is_definitely_bound = DiffingDict(self._is_definitely_bound)
        return _Context(self._references, is_definitely_bound, self._deferred)
    
    def unify(self, contexts):
        is_definitely_bound_mappings = [
            context._is_definitely_bound._new
            for context in contexts
        ]
        # We can pick an arbitrary mapping since if it's missing a name,
        # we already know that name is not definitely bound
        mapping = is_definitely_bound_mappings[0]
        
        for declaration in mapping:
            if not self._is_definitely_bound.get(declaration, False):
                self._is_definitely_bound[declaration] = all(
                    mapping.get(declaration, False)
                    for mapping in is_definitely_bound_mappings
                )
    
    
    def after_branch(self, branch_context):
        for declaration, is_bound in branch_context._is_definitely_bound._new.items():
            if not is_bound:
                self._is_definitely_bound[declaration] = False
    
    def add_deferred(self, node, update):
        declaration = self._references.referenced_declaration(node)
        self._deferred[declaration] = update
    
    def update_deferred(self):
        for declaration in list(self._deferred.keys()):
            self.is_declaration_definitely_bound(declaration)


class Bindings(object):
    def __init__(self, references, is_definitely_bound):
        self._references = references
        self._is_definitely_bound = is_definitely_bound
    
    def is_definitely_bound(self, node):
        declaration = self._references.referenced_declaration(node)
        return self.is_declaration_definitely_bound(declaration)
    
    def is_declaration_definitely_bound(self, declaration):
        return self._is_definitely_bound.get(declaration, False)


class DiffingDict(object):
    def __init__(self, original, new=None):
        if new is None:
            new = {}
        
        self._original = original
        self._new = new
    
    def __iter__(self):
        return iter(list(self._original) + list(self._new))
    
    def __getitem__(self, key):
        if key in self._new:
            return self._new[key]
        else:
            return self._original[key]
    
    def get(self, key, default=None):
        return self._new.get(key, self._original.get(key, default))
    
    def __setitem__(self, key, value):
        self._new[key] = value
    
    def __contains__(self, key):
        return key in self._new or key in self._original


def _copy_dict(values):
    if isinstance(values, dict):
        return values.copy()
    else:
        return values.flattened_copy()
