from .. import nodes, types, name_declaration, name_resolution, name_binding, builtins, util
from .expressions import ExpressionTypeInferer
from .statements import StatementTypeChecker
from ..identity_dict import IdentityDict


def check(module, source_tree=None, module_path=None):
    checker = _TypeChecker(source_tree, module_path, module.is_executable)
    module_type = checker.check(module)
    return module_type, checker.type_lookup()


class _TypeChecker(object):
    def __init__(self, source_tree, module_path, is_executable):
        self._source_tree = source_tree
        self._module_path = module_path
        self._type_lookup = IdentityDict()
        self._expression_type_inferer = ExpressionTypeInferer(self._type_lookup)
        self._statement_type_checker = StatementTypeChecker(self._expression_type_inferer, source_tree, module_path, is_executable)
    
    def type_lookup(self):
        return types.TypeLookup(self._type_lookup)
    
    def infer(self, expression, context):
        return self._expression_type_inferer.infer(expression, context)

    def update_context(self, statement, context):
        self._statement_type_checker.update_context(statement, context)

    def check(self, module):
        declarations = builtins.declarations()
        
        declaration_finder = name_declaration.DeclarationFinder()
        name_resolver = name_resolution.NameResolver(declaration_finder)
        references = name_resolver.resolve(module, declarations)
    
        context = builtins.module_context(references)
        for statement in module.body:
            self.update_context(statement, context)
        
        module_declarations = declaration_finder.declarations_in_module(module)
        exported_names = util.exported_names(module)
        exported_declarations = [
            module_declarations.declaration(name)
            for name in exported_names
        ]
        
        bindings = builtins.module_bindings(references)
        name_binding.update_bindings(module, bindings)
        
        return types.module(self._module_path, [
            # TODO: set read_only as appropriate
            types.attr(declaration.name, context.lookup_declaration(declaration))
            for declaration in exported_declarations
            # TODO: only use bound names
            #~ if context.is_bound(name)
        ])
        


    
