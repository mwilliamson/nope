from . import types, nodes


def infer(expression, context):
    return _inferers[type(expression)](expression, context)

def update_context(statement, context):
    return _checkers[type(statement)](statement, context)

def check(module):
    context = new_module_context()
    for statement in module.body:
        update_context(statement, context)

class Context(object):
    def __init__(self, bindings, return_type=None):
        self._vars = bindings
        self.return_type = return_type
    
    def add(self, name, binding):
        # TODO: prohibit overrides
        self._vars[name] = binding
    
    def lookup(self, name):
        return self._vars[name]
    
    def enter_func(self, return_type, local_names):
        func_vars = self._vars.copy()
        for local_name in local_names:
            func_vars[local_name] = None
        return Context(func_vars, return_type=return_type)
    
    def enter_module(self):
        return Context(self._vars.copy(), return_type=None)


module_context = Context({
    "int": types.type(types.int),
    "str": types.type(types.str),
    "none": types.type(types.none_type),
    "print": types.func([types.object], types.none_type),
})

def new_module_context():
    return module_context.enter_module()


def _infer_none(node, context):
    return types.none_type

def _infer_int(node, context):
    return types.int

def _infer_str(node, context):
    return types.str

def _infer_ref(node, context):
    ref_type = context.lookup(node.name)
    if ref_type is None:
        raise UnboundLocalError(node.name)
    else:
        return ref_type

def _infer_call(node, context):
    func_type = infer(node.func, context)
    
    if len(func_type.params) - 1 != len(node.args):
        raise ArgumentsLengthError(expected=len(func_type.params) - 1, actual=len(node.args))
    
    for actual_arg, formal_arg_type in zip(node.args, func_type.params[:-1]):
        actual_arg_type = infer(actual_arg, context)
        if not types.is_sub_type(formal_arg_type, actual_arg_type):
            raise TypeMismatchError(expected=formal_arg_type, actual=actual_arg_type)
    
    return infer(node.func, context).params[-1]

def _infer_function_def(node, context):
    def read_annotation(annotation):
        if annotation is None:
            return types.none_type
        else:
            result = infer(annotation, context)
            return result.type
    
    return_type = read_annotation(node.return_annotation)
        
    return types.func(
        [read_annotation(arg.annotation) for arg in node.args.args],
        return_type
    )

def _check_function_def(node, context):
    func_type = _infer_function_def(node, context)
    return_type = func_type.params[-1]
    
    arg_names = [arg.name for arg in node.args.args]
    
    local_names = arg_names + [
        child.name
        for child in node.body
        if _is_variable_binder(child)
    ]
    
    body_context = context.enter_func(return_type, local_names=local_names)
    
    for arg, arg_type in zip(node.args.args, func_type.params):
        body_context.add(arg.name, arg_type)
        
    for statement in node.body:
        update_context(statement, body_context)
        
    context.add(node.name, func_type)


def _is_variable_binder(node):
    return isinstance(node, (nodes.FunctionDef, nodes.Assignment))
    

_inferers = {
    nodes.NoneExpression: _infer_none,
    nodes.IntExpression: _infer_int,
    nodes.StringExpression: _infer_str,
    nodes.VariableReference: _infer_ref,
    nodes.Call: _infer_call,
}


def _check_expression_statement(node, context):
    infer(node.value, context)


def _check_return(node, context):
    expected = context.return_type
    actual = infer(node.value, context)
    if not types.is_sub_type(expected, actual):
        raise TypeMismatchError(expected, actual)


def _check_assignment(node, context):
    context.add(node.name, infer(node.value, context))


_checkers = {
    nodes.ExpressionStatement: _check_expression_statement,
    nodes.ReturnStatement: _check_return,
    nodes.Assignment: _check_assignment,
    nodes.FunctionDef: _check_function_def,
}


class TypeCheckError(Exception):
    pass


class ArgumentsLengthError(TypeCheckError):
    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual


class TypeMismatchError(TypeCheckError):
    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual
        
    def __str__(self):
        return "Expected {0} but was {1}".format(self.expected, self.actual)


class UnboundLocalError(TypeCheckError):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return "local variable {0} referenced before assignment".format(self.name)
