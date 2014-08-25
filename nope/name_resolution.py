from nope import nodes, errors


def resolve(node, context):
    return _resolvers[type(node)](node, context)


def _resolve_target(target, context):
    if isinstance(target, nodes.VariableReference) and not context.is_defined(target.name):
        context.define(target.name, target)
    
    resolve(target, context)



def _resolve_statements(statements, context):
    for statement in statements:
        resolve(statement, context)


def _resolve_nothing(node, context):
    pass


def _resolve_variable_reference(node, context):
    if not context.is_defined(node.name):
        raise errors.UndefinedNameError(node, node.name)
    context.add_reference(node)


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
        if isinstance(target, nodes.VariableReference) and not context.is_defined(target.name):
            context.define(target.name, target)
        
        resolve(target, context)


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
}


class Context(object):
    def __init__(self, definitions, variable_declaration_nodes, references):
        self._definitions = definitions
        self._variable_declaration_nodes = variable_declaration_nodes
        self._references = references
    
    def define(self, name, node):
        declaration_node = self._variable_declaration_node(name)
        self._definitions[name] = VariableDeclaration(declaration_node, is_definitely_bound=True)
        return declaration_node
    
    def _variable_declaration_node(self, name):
        if name not in self._variable_declaration_nodes:
            self._variable_declaration_nodes[name] = VariableDeclarationNode(name)
        return self._variable_declaration_nodes[name]
    
    def definition(self, name):
        return self._definitions[name].node
    
    def is_defined(self, name):
        return name in self._definitions
    
    def is_definitely_bound(self, name):
        return self._definitions[name].is_definitely_bound
    
    def add_reference(self, reference):
        definition = self.definition(reference.name)
        self._references[id(reference)] = definition
    
    def resolve(self, node):
        return self._references[id(node)]
    
    def enter_branch(self):
        return Context(BlockVars(self._definitions), self._variable_declaration_nodes, self._references)
    
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
            if not self.is_defined(name):
                declaration_node = self._variable_declaration_node(name)
                definitions = [
                    definitions.get(name, VariableDeclaration.unbound(declaration_node))
                    for definitions in new_definitions
                ]
                is_definitely_bound = bind and all(definition.is_definitely_bound for definition in definitions)
                self._definitions[name] = VariableDeclaration(declaration_node, is_definitely_bound)



class VariableDeclarationNode(object):
    # For variables, we introduce a separate node for declarations since
    # there are multiple candidate nodes to declare the node
    
    def __init__(self, name):
        self.name = name


class VariableDeclaration(object):
    @staticmethod
    def unbound(node):
        return VariableDeclaration(node, is_definitely_bound=False)
    
    def __init__(self, node, is_definitely_bound):
        self.node = node
        self.is_definitely_bound = is_definitely_bound
    


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
