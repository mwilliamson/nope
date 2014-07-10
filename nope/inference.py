from . import types, nodes


def infer(expression, context=None):
    if context is None:
        context = Context({})
    return _inferers[type(expression)](expression, context)

def update_context(statement, context):
    return _checkers[type(statement)](statement, context)

class Context(object):
    def __init__(self, bindings, return_type=None):
        self._vars = bindings
        self.return_type = return_type
    
    def add(self, name, binding):
        # TODO: prohibit overrides
        self._vars[name] = binding
    
    def lookup(self, name):
        return self._vars[name]
    
    def enter_func(self, return_type):
        return Context(self._vars, return_type)
    
    def enter_module(self):
        return Context(self._vars, return_type=None)


module_context = Context({
    "int": types.type(types.int),
    "str": types.type(types.str),
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
    return context.lookup(node.name)

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
    
    body_context = context.enter_func(return_type)
    for statement in node.body:
        update_context(statement, body_context)
        
    context.add(node.name, func_type)

_inferers = {
    nodes.NoneExpression: _infer_none,
    nodes.IntExpression: _infer_int,
    nodes.StringExpression: _infer_str,
    nodes.VariableReference: _infer_ref,
}


def _check_return(node, context):
    expected = context.return_type
    actual = infer(node.value)
    if not types.is_sub_type(expected, actual):
        raise TypeMismatchError(expected, actual)
    

_checkers = {
    nodes.ReturnStatement: _check_return,
    nodes.FunctionDef: _check_function_def,
}


class TypeMismatchError(Exception):
    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual
