import zuice

from . import nodes, errors, name_declaration


class LocalModule(object):
    def __init__(self, path, node):
        self.path = path
        self.node = node


class BuiltinModule(object):
    def __init__(self, name, type_):
        self.name = name
        self.type = type_


class ExportedNames(zuice.Base):
    _declaration_finder = zuice.dependency(name_declaration.DeclarationFinder)
    
    def for_module(self, module_node):
        export_names = None
        
        for statement in module_node.body:
            if (isinstance(statement, nodes.Assignment) and
                    any(isinstance(target, nodes.VariableReference) and target.name == "__all__" for target in statement.targets)):
                if not isinstance(statement.value, nodes.ListLiteral):
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
                name for name in self._declaration_finder.declarations_in_module(module_node).names()
                if not name.startswith("_")
            ]
        else:
            return export_names


def _all_wrong_type_error(node):
    return errors.AllAssignmentError(node, "__all__ must be a list of string literals")
