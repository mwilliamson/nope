from . import nodes


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
    else:
        return []


def exported_names(module):
    export_names = [
        name for name in declared_locals(module.body)
        if not name.startswith("_")
    ]
    
    for statement in module.body:
        if isinstance(statement, nodes.Assignment) and "__all__" in statement.targets:
            # TODO: raise more appropriate error (and add test)
            assert isinstance(statement.value, nodes.ListExpression)
            
            def extract_string_value(node):
                # TODO: raise more appropriate error (and add test)
                assert isinstance(node, nodes.StringExpression)
                return node.value
            
            # TODO: raise error if already defined
            export_names = [
                extract_string_value(element)
                for element in statement.value.elements
            ]
            
    
    return export_names
