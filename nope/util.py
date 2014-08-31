from . import nodes, errors, name_declaration


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
        declaration_finder = name_declaration.DeclarationFinder()
        return [
            name for name in declaration_finder.declarations_in_module(module).names()
            if not name.startswith("_")
        ]
    else:
        return export_names


def _all_wrong_type_error(node):
    return errors.AllAssignmentError(node, "__all__ must be a list of string literals")
