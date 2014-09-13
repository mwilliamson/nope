from nope import nodes, errors, util, visit, name_declaration, types
from nope.identity_dict import IdentityDict


def check_bindings(node, references, type_lookup, is_definitely_bound):
    context = _Context(references, is_definitely_bound, set())
    checker = _BindingChecker(type_lookup)
    checker.update_bindings(node, context)
    return Bindings(references, context._is_definitely_bound)


class _BindingChecker(object):
    def __init__(self, type_lookup):
        self._type_lookup = type_lookup
    
    def update_bindings(self, node, context):
        visitor = visit.Visitor()
        visitor.before(nodes.VariableReference, self._check_variable_reference)
        visitor.replace(nodes.Assignment, self._update_assignment_binding)
        visitor.replace(nodes.IfElse, self._update_if_else)
        visitor.replace(nodes.WhileLoop, self._update_while_loop)
        visitor.replace(nodes.ForLoop, self._update_for_loop)
        visitor.replace(nodes.TryStatement, self._update_try)
        visitor.replace(nodes.WithStatement, self._update_with)
        visitor.replace(nodes.FunctionDef, self._update_function_definition)
        visitor.before(nodes.Argument, self._update_argument)
        visitor.replace(nodes.ClassDefinition, self._update_class_definition)
        visitor.before(nodes.Import, self._update_import)
        visitor.before(nodes.ImportFrom, self._update_import)
        
        return visitor.visit(node, context)


    def _check_variable_reference(self, visitor, node, context):
        if not context.is_definitely_bound(node):
            raise errors.UnboundLocalError(node, node.name)


    def _update_target(self, visitor, target, context):
        if isinstance(target, nodes.TupleLiteral):
            for element in target.elements:
                self._update_target(visitor, element, context)
        else:
            if isinstance(target, nodes.VariableReference):
                context.bind(target)
            visitor.visit(target, context)


    def _update_assignment_binding(self, visitor, node, context):
        visitor.visit(node.value, context)
        
        for target in node.targets:
            self._update_target(visitor, target, context)


    def _update_if_else(self, visitor, node, context):
        visitor.visit(node.condition, context)
        
        self._update_branches(
            visitor,
            [_branch(node.true_body), _branch(node.false_body)],
            context,
            bind=True,
        )


    def _update_while_loop(self, visitor, node, context):
        visitor.visit(node.condition, context)
        
        self._update_branches(
            visitor,
            [_branch(node.body), _branch(node.else_body)],
            context,
            bind=False,
        )


    def _update_for_loop(self, visitor, node, context):
        visitor.visit(node.iterable, context)
        
        def update_for_loop_target(branch_context):
            self._update_target(visitor, node.target, branch_context)
        
        self._update_branches(
            visitor,
            [
                _branch(node.body, before=update_for_loop_target),
                _branch(node.else_body)
            ],
            context,
            bind=False,
        )


    def _update_try(self, visitor, node, context):
        branches = [_branch(node.body), _branch(node.finally_body)]
        
        def create_handler_branch(handler):
            if handler.type is not None:
                visitor.visit(handler.type, context)
                
            def update_handler_target(branch_context):
                if handler.target is not None:
                    self._update_target(visitor, handler.target, branch_context)
                    branch_context.add_exception_handler_target(handler.target)
            
            def delete_handler_target(branch_context):
                if handler.target is not None:
                    context.delete_exception_handler_target(handler.target)
            
            return _branch(
                handler.body,
                before=update_handler_target,
                after=delete_handler_target,
            )
        
        for handler in node.handlers:
            branches.append(create_handler_branch(handler))
        
        self._update_branches(
            visitor,
            branches,
            context,
            bind=False,
        )


    def _update_with(self, visitor, node, context):
        visitor.visit(node.value, context)
        
        exit_type = self._type_of(node.value).attrs.type_of("__exit__")
        # TODO: this is duplicated in codegeneration
        while not types.is_func_type(exit_type):
            exit_type = exit_type.attrs.type_of("__call__")
        
        def update_with_target(branch_context):
            if node.target is not None:
                self._update_target(visitor, node.target, branch_context)
        
        self._update_branches(
            visitor,
            [_branch(node.body, before=update_with_target)],
            context,
            bind=exit_type.return_type == types.none_type,
        )


    def _update_function_definition(self, visitor, node, context):
        context.bind(node)
        body_context = context.enter_new_namespace()
        for arg in node.args.args:
            visitor.visit(arg, body_context)
        
        for statement in node.body:
            visitor.visit(statement, body_context)


    def _update_argument(self, visitor, node, context):
        context.bind(node)

    
    def _update_class_definition(self, visitor, node, context):
        context.bind(node)
        body_context = context.enter_new_namespace()
        for statement in node.body:
            visitor.visit(statement, body_context)
    
    
    def _update_import(self, visitor, node, context):
        for alias in node.names:
            context.bind(alias)
        

    def _update_branches(self, visitor, branches, context, bind=False):
        branch_contexts = [
            self._update_branch(visitor, branch, context)
            for branch in branches
        ]
        if bind:
            context.unify(branch_contexts)


    def _update_branch(self, visitor, branch, context):
        branch_context = branch.enter_context(context)
        self._update_statements(visitor, branch.statements, branch_context)
        branch.exit_context(context)
        return branch_context


    def _update_statements(self, visitor, statements, context):
        for statement in statements:
            visitor.visit(statement, context)
    
    def _type_of(self, node):
        return self._type_lookup.type_of(node)


class _Branch(object):
    def __init__(self, statements, before=None, after=None):
        self.statements = statements
        self._before = before
        self._after = after
    
    def enter_context(self, context):
        branch_context = context.enter_branch()
        if self._before is not None:
            self._before(branch_context)
        return branch_context
    
    def exit_context(self, context):
        if self._after is not None:
            self._after(context)

_branch = _Branch


class _Context(object):
    def __init__(self, declarations, is_definitely_bound, exception_handler_target_names):
        self._declarations = declarations
        self._is_definitely_bound = is_definitely_bound
        self._exception_handler_target_names = exception_handler_target_names
    
    def is_definitely_bound(self, node):
        declaration = self._declarations.referenced_declaration(node)
        return self.is_declaration_definitely_bound(declaration)
    
    def is_declaration_definitely_bound(self, declaration):
        return self._is_definitely_bound.get(declaration, False)
    
    def bind(self, node):
        declaration = self._declarations.referenced_declaration(node)
        self._is_definitely_bound[declaration] = True
    
    def add_exception_handler_target(self, node):
        if node.name in self._exception_handler_target_names:
            raise errors.InvalidReassignmentError(node, "cannot reuse the same name for nested exception handler targets")
            
        self._exception_handler_target_names.add(node.name)
    
    def delete_exception_handler_target(self, node):
        self._exception_handler_target_names.remove(node.name)
    
    def enter_branch(self):
        return _Context(self._declarations, DiffingDict(self._is_definitely_bound), self._exception_handler_target_names)
    
    def enter_new_namespace(self):
        is_definitely_bound = _copy_dict(self._is_definitely_bound)
        for declaration in is_definitely_bound:
            if isinstance(declaration, name_declaration.ExceptionHandlerTargetNode):
                is_definitely_bound[declaration] = False
        return _Context(self._declarations, is_definitely_bound, set())
    
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
    
    def flattened_copy(self):
        copy = self._original.copy()
        copy.update(self._new)
        return copy
    
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
