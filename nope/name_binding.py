from nope import nodes, errors, util, visit, name_declaration


def update_bindings(node, context):
    visitor = visit.Visitor()
    visitor.before(nodes.VariableReference, _check_variable_reference)
    visitor.replace(nodes.Assignment, _update_assignment_binding)
    visitor.replace(nodes.IfElse, _update_if_else)
    visitor.replace(nodes.WhileLoop, _update_while_loop)
    visitor.replace(nodes.ForLoop, _update_for_loop)
    visitor.replace(nodes.TryStatement, _update_try)
    visitor.replace(nodes.FunctionDef, _update_function_definition)
    visitor.before(nodes.Argument, _update_argument)
    visitor.before(nodes.Import, _update_import)
    visitor.before(nodes.ImportFrom, _update_import)
    
    return visitor.visit(node, context)


def _check_variable_reference(visitor, node, context):
    if not context.is_definitely_bound(node):
        raise errors.UnboundLocalError(node, node.name)


def _update_target(visitor, target, context):
    if isinstance(target, nodes.VariableReference):
        context.bind(target)
    visitor.visit(target, context)


def _update_assignment_binding(visitor, node, context):
    visitor.visit(node.value, context)
    
    for target in node.targets:
        _update_target(visitor, target, context)


def _update_if_else(visitor, node, context):
    visitor.visit(node.condition, context)
    
    _update_branches(
        [_branch(node.true_body), _branch(node.false_body)],
        context,
        bind=True,
    )


def _update_while_loop(visitor, node, context):
    visitor.visit(node.condition, context)
    
    _update_branches(
        [_branch(node.body), _branch(node.else_body)],
        context,
        bind=False,
    )


def _update_for_loop(visitor, node, context):
    visitor.visit(node.iterable, context)
    
    def update_for_loop_target(branch_context):
        _update_target(visitor, node.target, branch_context)
    
    _update_branches(
        [
            _branch(node.body, before=update_for_loop_target),
            _branch(node.else_body)
        ],
        context,
        bind=False,
    )


def _update_try(visitor, node, context):
    branches = [_branch(node.body), _branch(node.finally_body)]
    
    def create_handler_branch(handler):
        if handler.type is not None:
            visitor.visit(handler.type, context)
            
        def update_handler_target(branch_context):
            if handler.target is not None:
                _update_target(visitor, handler.target, branch_context)
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
    
    _update_branches(
        branches,
        context,
        bind=False,
    )


def _update_function_definition(visitor, node, context):
    context.bind(node)
    body_context = context.enter_function()
    for arg in node.args.args:
        visitor.visit(arg, body_context)
    
    for statement in node.body:
        visitor.visit(statement, body_context)


def _update_argument(visitor, node, context):
    context.bind(node)


def _update_import(visitor, node, context):
    for alias in node.names:
        context.bind(alias)
    


def _update_branches(branches, context, bind=False):
    branch_contexts = [
        _update_branch(branch, context)
        for branch in branches
    ]
    if bind:
        context.unify(branch_contexts)


def _update_branch(branch, context):
    branch_context = branch.enter_context(context)
    _update_statements(branch.statements, branch_context)
    branch.exit_context(context)
    return branch_context


def _update_statements(statements, context):
    for statement in statements:
        # TODO: use visitor.visit instead
        update_bindings(statement, context)


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


class Context(object):
    def __init__(self, declarations, is_definitely_bound, exception_handler_target_names):
        self._declarations = declarations
        self._is_definitely_bound = is_definitely_bound
        self._exception_handler_target_names = exception_handler_target_names
    
    def is_definitely_bound(self, node):
        declaration = self._declarations[id(node)]
        return self._is_definitely_bound.get(declaration, False)
    
    def bind(self, node):
        declaration = self._declarations[id(node)]
        self._is_definitely_bound[declaration] = True
    
    def add_exception_handler_target(self, node):
        if node.name in self._exception_handler_target_names:
            raise errors.InvalidReassignmentError(node, "cannot reuse the same name for nested exception handler targets")
            
        self._exception_handler_target_names.add(node.name)
    
    def delete_exception_handler_target(self, node):
        self._exception_handler_target_names.remove(node.name)
    
    def enter_branch(self):
        return Context(self._declarations, DiffingDict(self._is_definitely_bound), self._exception_handler_target_names)
    
    def enter_function(self):
        is_definitely_bound = _copy_dict(self._is_definitely_bound)
        for declaration in is_definitely_bound:
            if isinstance(declaration, name_declaration.ExceptionHandlerTargetNode):
                is_definitely_bound[declaration] = False
        return Context(self._declarations, is_definitely_bound, set())
    
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
