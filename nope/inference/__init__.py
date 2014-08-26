from .. import nodes, types, name_declaration, name_resolution, name_binding, builtins, util
from .expressions import ExpressionTypeInferer
from .statements import StatementTypeChecker


def _resolve_references(node):
    references = builtins.references()
    return name_resolution.resolve(node, references)


def check(module, source_tree=None, module_path=None):
    references = _resolve_references(module)
    
    checker = _TypeChecker(source_tree, module_path, module.is_executable)
    module_type = checker.check(module, references)
    return module_type, checker.type_lookup()


class _TypeChecker(object):
    def __init__(self, source_tree, module_path, is_executable):
        self._source_tree = source_tree
        self._module_path = module_path
        self._type_lookup = {}
        self._expression_type_inferer = ExpressionTypeInferer(self._type_lookup)
        self._statement_type_checker = StatementTypeChecker(self._expression_type_inferer, source_tree, module_path, is_executable)
    
    def type_lookup(self):
        return types.TypeLookup(self._type_lookup)
    
    def infer(self, expression, context):
        return self._expression_type_inferer.infer(expression, context)

    def update_context(self, statement, context):
        self._statement_type_checker.update_context(statement, context)

    def check(self, module, references):
        context = builtins.module_context(references)
        for statement in module.body:
            self.update_context(statement, context)
        
        exported_names = util.exported_names(module)
        exported_declarations = [
            references.definition(name)
            for name in exported_names
        ]
        
        bindings = builtins.module_bindings(references)
        name_binding.update_bindings(module, bindings)
        
        return types.module(self._module_path, [
            # TODO: set read_only as appropriate
            types.attr(declaration.name, context.lookup_declaration(declaration))
            for declaration in exported_declarations
            #~ if context.is_bound(name)
        ])
        


    
