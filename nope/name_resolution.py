from nope import nodes, errors


def resolve(node, context):
    return _resolvers[type(node)](node, context)


def _resolve_target(target, context, target_type=None):
    if isinstance(target, nodes.VariableReference):
        context.define(target.name, target, target_type=target_type)
    
    resolve(target, context)



def _resolve_statements(statements, context):
    for statement in statements:
        resolve(statement, context)


def _resolve_nothing(node, context):
    pass


def _resolve_variable_reference(node, context):
    if not context.is_defined(node.name):
        raise errors.UndefinedNameError(node, node.name)
    context.add_reference(node, node.name)


def _resolve_list_expression(node, context):
    for element in node.elements:
        resolve(element, context)


def _resolve_call(node, context):
    resolve(node.func, context)
    for arg in node.args:
        resolve(arg, context)
    for arg in node.kwargs.values():
        resolve(arg, context)


def _resolve_attribute_access(node, context):
    resolve(node.value, context)


def _resolve_unary_operation(node, context):
    resolve(node.operand, context)


def _resolve_binary_operation(node, context):
    resolve(node.left, context)
    resolve(node.right, context)


def _resolve_subscript(node, context):
    resolve(node.value, context)
    resolve(node.slice, context)


def _resolve_return(node, context):
    if node.value is not None:
        resolve(node.value, context)


def _resolve_expression_statement(node, context):
    resolve(node.value, context)


def _resolve_assignment(node, context):
    resolve(node.value, context)
    
    for target in node.targets:
        _resolve_target(target, context)


def _resolve_if_else(node, context):
    resolve(node.condition, context)
    
    _resolve_branches(
        [_branch(node.true_body), _branch(node.false_body)],
        context,
        bind=True,
    )


def _resolve_while_loop(node, context):
    resolve(node.condition, context)
    
    _resolve_branches(
        [_branch(node.body), _branch(node.else_body)],
        context,
        bind=False,
    )


def _resolve_for_loop(node, context):
    resolve(node.iterable, context)
    
    def resolve_for_loop_target(branch_context):
        _resolve_target(node.target, branch_context)
    
    _resolve_branches(
        [
            _branch(node.body, before=resolve_for_loop_target),
            _branch(node.else_body)
        ],
        context,
        bind=False,
    )


def _resolve_try(node, context):
    branches = [_branch(node.body), _branch(node.finally_body)]
    
    def create_handler_branch(handler):
        if handler.type is not None:
            resolve(handler.type, context)
            
        def resolve_handler_target(branch_context):
            if handler.target is not None:
                _resolve_target(handler.target, branch_context, target_type=ExceptionHandlerTargetNode)
        
        return _branch(handler.body, before=resolve_handler_target)
    
    for handler in node.handlers:
        branches.append(create_handler_branch(handler))
    
    _resolve_branches(
        branches,
        context,
        bind=False,
    )


def _resolve_raise(node, context):
    resolve(node.value, context)


def _resolve_assert(node, context):
    resolve(node.condition, context)
    if node.message is not None:
        resolve(node.message, context)


def _resolve_function_def(node, context):
    body_context = context.enter_function()
    for arg in node.args.args:
        body_context.define(arg.name, arg)
        body_context.add_reference(arg, arg.name)
    
    _resolve_statements(node.body, body_context)


def _resolve_import(node, context):
    for alias in node.names:
        context.define(alias.value_name, alias, target_type=ImportDeclarationNode)
        context.add_reference(alias, alias.value_name)
    


def _resolve_branches(branches, context, bind=False):
    branch_contexts = [
        _resolve_branch(branch, context)
        for branch in branches
    ]
    return context.unify(branch_contexts, bind=bind)


def _resolve_branch(branch, context):
    branch_context = branch.enter_context(context)
    _resolve_statements(branch.statements, branch_context)
    return branch_context


class _Branch(object):
    def __init__(self, statements, before=None):
        self.statements = statements
        self._before = before
    
    def enter_context(self, context):
        branch_context = context.enter_branch()
        if self._before is not None:
            self._before(branch_context)
        return branch_context

_branch = _Branch


_resolvers = {
    nodes.NoneExpression: _resolve_nothing,
    nodes.BooleanExpression: _resolve_nothing,
    nodes.IntExpression: _resolve_nothing,
    nodes.StringExpression: _resolve_nothing,
    nodes.VariableReference: _resolve_variable_reference,
    nodes.ListExpression: _resolve_list_expression,
    nodes.Call: _resolve_call,
    nodes.AttributeAccess: _resolve_attribute_access,
    nodes.UnaryOperation: _resolve_unary_operation,
    nodes.BinaryOperation: _resolve_binary_operation,
    nodes.Subscript: _resolve_subscript,
    
    nodes.ReturnStatement: _resolve_return,
    nodes.ExpressionStatement: _resolve_expression_statement,
    nodes.Assignment: _resolve_assignment,
    nodes.IfElse: _resolve_if_else,
    nodes.WhileLoop: _resolve_while_loop,
    nodes.ForLoop: _resolve_for_loop,
    nodes.BreakStatement: _resolve_nothing,
    nodes.ContinueStatement: _resolve_nothing,
    nodes.TryStatement: _resolve_try,
    nodes.RaiseStatement: _resolve_raise,
    nodes.AssertStatement: _resolve_assert,
    nodes.FunctionDef: _resolve_function_def,
    
    nodes.Import: _resolve_import,
    nodes.ImportFrom: _resolve_import,
}


class Context(object):
    def __init__(self, definitions, variable_declaration_nodes, references):
        self._definitions = definitions
        self._variable_declaration_nodes = variable_declaration_nodes
        self._references = references
    
    def define(self, name, node, is_definitely_bound=True, target_type=None):
        if target_type is None:
            target_type = VariableDeclarationNode
        
        declaration_node = self._variable_declaration_node(name, node, target_type)
        self._definitions[name] = VariableDeclaration(
            declaration_node,
            is_definitely_bound=is_definitely_bound,
        )
        return declaration_node
    
    def _variable_declaration_node(self, name, target_node, target_type):
        if name in self._variable_declaration_nodes:
            node = self._variable_declaration_nodes[name]
            node_type = type(node)
            if not node_type == target_type:
                raise errors.InvalidReassignmentError(
                    target_node,
                    "{} and {} cannot share the same name".format(target_type.description, type(node).description)
                )
            if target_type == ExceptionHandlerTargetNode and self.is_defined(name) and self.is_definitely_bound(name):
                raise errors.InvalidReassignmentError(
                    target_node,
                    "cannot reuse the same name for nested exception handler targets"
                )
        else:
            node = self._variable_declaration_nodes[name] = target_type(name)
        
        return node
    
    def definition(self, name):
        return self._definitions[name].node

    def is_defined(self, name):
        return name in self._definitions
    
    def is_definitely_bound(self, name):
        return self._definitions[name].is_definitely_bound
    
    def add_reference(self, reference, name):
        definition = self.definition(name)
        self._references[id(reference)] = definition
    
    def resolve(self, node):
        return self._references[id(node)]
    
    def enter_branch(self):
        return Context(BlockVars(self._definitions), self._variable_declaration_nodes, self._references)
    
    def enter_function(self):
        # TODO: test that shadowed variables are unbound even if outer scope
        # has bound variable of the same name
        return Context(self._definitions.copy(), {}, self._references)
    
    def unify(self, contexts, bind):
        new_definitions = [
            context._definitions._new_definitions
            for context in contexts
        ]
        new_names = set(
            name
            for definitions in new_definitions
            for name in definitions
        )
        
        for name in new_names:
            if not self.is_defined(name) or not self.is_definitely_bound(name):
                definitions = [
                    definitions.get(name, UnboundName())
                    for definitions in new_definitions
                ]
                node_types = set(type(definition.node) for definition in definitions if definition.node is not None)
                # This assertion should never fail since the call to
                # self._variable_declaration_node in self.define should fail
                # if the target type is inconsistent
                assert len(node_types) == 1
                node_type, = node_types
                
                declaration_node = self._variable_declaration_node(name, None, node_type)
                is_definitely_bound = bind and all(definition.is_definitely_bound for definition in definitions)
                self._definitions[name] = VariableDeclaration(declaration_node, is_definitely_bound)



class VariableDeclarationNode(object):
    # For variables, we introduce a separate node for declarations since
    # there are multiple candidate nodes to declare the node
    
    description = "variable assignment"
    
    def __init__(self, name):
        self.name = name


class ExceptionHandlerTargetNode(object):
    description = "exception handler target"
    
    def __init__(self, name):
        self.name = name


class ImportDeclarationNode(object):
    description = "import statement"
    
    def __init__(self, name):
        self.name = name


class VariableDeclaration(object):
    def __init__(self, node, is_definitely_bound):
        self.node = node
        self.is_definitely_bound = is_definitely_bound


class UnboundName(object):
    node = None
    is_definitely_bound = False



class BlockVars(object):
    def __init__(self, definitions):
        self._original_definitions = definitions
        self._new_definitions = {}
    
    def __getitem__(self, key):
        if key in self._new_definitions:
            return self._new_definitions[key]
        else:
            return self._original_definitions[key]
    
    def __setitem__(self, key, value):
        self._new_definitions[key] = value
    
    def __contains__(self, key):
        return key in self._new_definitions or key in self._original_definitions
