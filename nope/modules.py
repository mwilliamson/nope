import os

import zuice

from . import nodes, errors, name_declaration


class Module(object):
    def __init__(self):
        raise Exception("Module is abstract")


class ModuleTypes(object):
    pass


class LocalModule(Module):
    def __init__(self, path, node):
        self.path = path
        self.node = node
    
    def __repr__(self):
        return "LocalModule({})".format(repr(self.path))


class BuiltinModule(Module):
    def __init__(self, name, type_):
        self.name = name
        self.type = type_
    
    @property
    def path(self):
        return os.path.join(os.path.dirname(__file__), "../stdlib", self.name + ".py")


class ModuleExports(zuice.Base):
    _declaration_finder = zuice.dependency(name_declaration.DeclarationFinder)
    
    def names(self, module_node):
        return [
            declaration.name
            for declaration in self.declarations(module_node)
        ]
    
    def declarations(self, module_node):
        export_declarations = self._export_declarations(module_node.body)
        module_declarations = self._declaration_finder.declarations_in(module_node)
        
        if len(export_declarations) == 0:
            return [
                declaration for declaration in module_declarations
                if not declaration.name.startswith("_")
            ]
        elif len(export_declarations) == 1:
            statement, = export_declarations
            
            if not isinstance(statement.value, nodes.ListLiteral):
                raise _all_wrong_type_error(statement)
            
            names = [
                _extract_string_value_from_literal(statement, element)
                for element in statement.value.elements
            ]
            return list(map(module_declarations.declaration, names))
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
    if isinstance(node, nodes.StringLiteral):
        return node.value
    else:
        raise _all_wrong_type_error(statement)


def _all_wrong_type_error(node):
    return errors.AllAssignmentError(node, "__all__ must be a list of string literals")
