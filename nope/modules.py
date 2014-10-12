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


class ModuleExports(zuice.Base):
    _declaration_finder = zuice.dependency(name_declaration.DeclarationFinder)
    
    def names(self, module_node):
        export_declarations = self._export_declarations(module_node.body)
        
        if len(export_declarations) == 0:
            return [
                name for name in self._declaration_finder.declarations_in_module(module_node).names()
                if not name.startswith("_")
            ]
        elif len(export_declarations) == 1:
            statement, = export_declarations
            
            if not isinstance(statement.value, nodes.ListLiteral):
                raise _all_wrong_type_error(statement)
            
            return [
                _extract_string_value_from_literal(statement, element)
                for element in statement.value.elements
            ]
        else:
            raise errors.AllAssignmentError(export_declarations[1], "__all__ cannot be redeclared")
    
    def _export_declarations(self, statements):
        return list(filter(self._is_export_declaration, statements))
    
    def _is_export_declaration(self, statement):
        return (
            isinstance(statement, nodes.Assignment) and
            any(
                isinstance(target, nodes.VariableReference) and
                target.name == "__all__" for target in statement.targets
            )
        )


def _extract_string_value_from_literal(statement, node):
    if isinstance(node, nodes.StringExpression):
        return node.value
    else:
        raise _all_wrong_type_error(statement)


def _all_wrong_type_error(node):
    return errors.AllAssignmentError(node, "__all__ must be a list of string literals")
