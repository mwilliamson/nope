from .. import nodes, types, name_declaration, name_resolution, name_binding, builtins, util
from .expressions import ExpressionTypeInferer
from .statements import StatementTypeChecker
from ..identity_dict import IdentityDict


def check(module, module_resolver=None, module_types=None):
    # TODO: don't construct the type checker with a module
    checker = _TypeChecker(name_declaration.DeclarationFinder(), module_types, module_resolver, module)
    module_type = checker.check(module)
    return module_type, checker.type_lookup()


class _TypeChecker(object):
    def __init__(self, declaration_finder, module_types, module_resolver, module):
        self._declaration_finder = declaration_finder
        self._module_path = module.path
        self._type_lookup = IdentityDict()
        self._expression_type_inferer = ExpressionTypeInferer(self._type_lookup)
        self._statement_type_checker = StatementTypeChecker(declaration_finder, self._expression_type_inferer, module_resolver, module_types, module)
    
    def type_lookup(self):
        return types.TypeLookup(self._type_lookup)
    
    def infer(self, expression, context):
        return self._expression_type_inferer.infer(expression, context)

    def update_context(self, statement, context):
        self._statement_type_checker.update_context(statement, context)

    def check(self, module):
        declarations = builtins.declarations()
        
        name_resolver = name_resolution.NameResolver(self._declaration_finder, declarations)
        references = name_resolver.resolve(module.node)
    
        context = builtins.module_context(references)
        for statement in module.node.body:
            self.update_context(statement, context)
        
        module_declarations = self._declaration_finder.declarations_in_module(module.node)
        exported_names = util.exported_names(module.node)
        exported_declarations = [
            module_declarations.declaration(name)
            for name in exported_names
        ]
        
        builtin_is_definitely_bound = builtins.module_bindings(references)
        bindings = name_binding.check_bindings(
            module.node,
            references=references,
            type_lookup=self.type_lookup(),
            is_definitely_bound=builtin_is_definitely_bound,
        )
        
        return types.module(module.path, [
            # TODO: set read_only as appropriate
            types.attr(declaration.name, context.lookup_declaration(declaration))
            for declaration in exported_declarations
            if bindings.is_declaration_definitely_bound(declaration)
        ])
        


    
