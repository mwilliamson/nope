import collections

from . import nodes, errors


def declared_locals(statements):
    names = OrderedSet([])
    for child in statements:
        names |= declared_names(child)
    
    return names


def declared_names(node):
    if isinstance(node, nodes.FunctionDef):
        return OrderedSet([node.name])
    elif isinstance(node, nodes.Assignment):
        return _target_names(node.targets)
    elif isinstance(node, (nodes.ImportFrom, nodes.Import)):
        return OrderedSet([alias.value_name for alias in node.names])
    elif isinstance(node, nodes.IfElse):
        return declared_locals(node.true_body) | declared_locals(node.false_body)
    elif isinstance(node, nodes.ForLoop):
        return _target_names([node.target]) | declared_locals(node.body)
    elif isinstance(node, nodes.WhileLoop):
        return declared_locals(node.body) | declared_locals(node.else_body)
    else:
        return OrderedSet([])


def _target_names(targets):
    return OrderedSet([
        target.name
        for target in targets
        if isinstance(target, nodes.VariableReference)
    ])


class OrderedSet(object):
    def __init__(self, values):
        self._values = collections.OrderedDict.fromkeys(values)
    
    def copy(self):
        return OrderedSet(self._values.keys())
    
    def __or__(self, other):
        values = self.copy()
        values |= other
        return values
    
    def __ior__(self, other):
        self._values.update(other._values)
        return self
    
    def __iter__(self):
        return iter(self._values)



def exported_names(module):
    export_names = None
    
    for statement in module.body:
        if (isinstance(statement, nodes.Assignment) and
                any(isinstance(target, nodes.VariableReference) and target.name == "__all__" for target in statement.targets)):
            if not isinstance(statement.value, nodes.ListExpression):
                raise _all_wrong_type_error(statement)
            
            def extract_string_value(node):
                if isinstance(node, nodes.StringExpression):
                    return node.value
                else:
                    raise _all_wrong_type_error(statement)
            
            if export_names is None:
                export_names = [
                    extract_string_value(element)
                    for element in statement.value.elements
                ]
            else:
                raise errors.AllAssignmentError(statement, "__all__ cannot be redeclared")
    
    if export_names is None:
        return [
            name for name in declared_locals(module.body)
            if not name.startswith("_")
        ]
    else:
        return export_names


def _all_wrong_type_error(node):
    return errors.AllAssignmentError(node, "__all__ must be a list of string literals")
