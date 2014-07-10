from . import types, nodes


def infer(node, context=None):
    if context is None:
        context = Context({})
    return _inferers[type(node)](node, context)


class Context(object):
    def __init__(self, bindings):
        self._vars = bindings
    
    def lookup(self, name):
        return self._vars[name]


module_context = Context({
    "int": types.type(types.int),
    "str": types.type(types.str),
})

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
        
    return types.func(
        [read_annotation(arg.annotation) for arg in node.args.args],
        read_annotation(node.return_annotation)
    )

_inferers = {
    nodes.NoneExpression: _infer_none,
    nodes.IntExpression: _infer_int,
    nodes.StringExpression: _infer_str,
    nodes.VariableReference: _infer_ref,
    
    nodes.FunctionDef: _infer_function_def,
}
