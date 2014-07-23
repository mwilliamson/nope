from . import nodes


def declared_locals(func_def):
    return [
        child.name
        for child in func_def.body
        if _is_variable_binder(child)
    ]


def _is_variable_binder(node):
    return isinstance(node, (nodes.FunctionDef, nodes.Assignment))
