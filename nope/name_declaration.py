from nope import nodes, errors, util, visit


def declare(node, context):
    visitor = visit.Visitor()
    visitor.before(nodes.Assignment, _declare_assignment)
    visitor.before(nodes.ForLoop, _declare_for_loop)
    visitor.before(nodes.TryStatement, _declare_try)
    visitor.replace(nodes.FunctionDef, _declare_function_def)
    visitor.before(nodes.Argument, _declare_argument)
    visitor.before(nodes.Import, _declare_import)
    visitor.before(nodes.ImportFrom, _declare_import)
    
    return visitor.visit(node, context)


def _declare_target(target, context, target_type):
    if isinstance(target, nodes.VariableReference):
        context.declare(target.name, target, target_type=target_type)


def _declare_assignment(visitor, node, context):
    for target in node.targets:
        _declare_target(target, context, target_type=VariableDeclarationNode)


def _declare_for_loop(visitor, node, context):
    _declare_target(node.target, context, target_type=VariableDeclarationNode)


def _declare_try(visitor, node, context):
    for handler in node.handlers:
        if handler.target is not None:
            _declare_target(handler.target, context, target_type=ExceptionHandlerTargetNode)


def _declare_function_def(visitor, node, context):
    context.declare(node.name, node, target_type=FunctionDeclarationNode)


def _declare_argument(visitor, node, context):
    context.declare(node.name, node, target_type=VariableDeclarationNode)


def _declare_import(visitor, node, context):
    for alias in node.names:
        context.declare(alias.value_name, alias, target_type=ImportDeclarationNode)


class Context(object):
    def __init__(self, declarations):
        self._declarations = declarations
    
    def declare(self, name, target_node, target_type):
        if name in self._declarations:
            declaration_node = self._declarations[name]
            node_type = type(declaration_node)
            if node_type != target_type:
                raise errors.InvalidReassignmentError(
                    target_node,
                    "{} and {} cannot share the same name".format(target_type.description, node_type.description)
                )
        else:
            declaration_node = self._declarations[name] = target_type(name)
        
        return declaration_node
    
    def declaration(self, name):
        return self._declarations[name]
    
    def is_declared(self, name):
        return name in self._declarations


class VariableDeclarationNode(object):
    description = "variable assignment"
    
    def __init__(self, name):
        self.name = name


class ExceptionHandlerTargetNode(object):
    description = "exception handler target"
    
    def __init__(self, name):
        self.name = name


class FunctionDeclarationNode(object):
    description = "function declaration"
    
    def __init__(self, name):
        self.name = name


class ImportDeclarationNode(object):
    description = "import statement"
    
    def __init__(self, name):
        self.name = name


def declarations_in_function(node):
    context = Context({})
    
    for arg in node.args.args:
        declare(arg, context)
    
    for statement in node.body:
        declare(statement, context)
        
    return context._declarations
