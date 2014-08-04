from . import nodes, errors, types


def declared_locals(statements):
    names = []
    for child in statements:
        names += declared_names(child)
    
    return names


def declared_names(node):
    if isinstance(node, nodes.FunctionDef):
        return [node.name]
    elif isinstance(node, nodes.Assignment):
        return node.targets
    elif isinstance(node, (nodes.ImportFrom, nodes.Import)):
        return [alias.value_name for alias in node.names]
    elif isinstance(node, nodes.IfElse):
        return declared_locals(node.true_body) + declared_locals(node.false_body)
    else:
        return []



def exported_names(module):
    export_names = None
    
    for statement in module.body:
        if isinstance(statement, nodes.Assignment) and "__all__" in statement.targets:
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
