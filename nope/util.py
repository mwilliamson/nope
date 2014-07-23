from . import nodes


def declared_locals(func_def):
    names = []
    for child in func_def.body:
        names += _declared_names(child)
    
    return names


def _declared_names(node):
    if isinstance(node, nodes.FunctionDef):
        return [node.name]
    elif isinstance(node, nodes.Assignment):
        return node.targets
    else:
        return []
