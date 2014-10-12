import zuice

from .. import nodes, types, name_declaration, name_resolution, name_binding, builtins, module_resolution, modules
from .expressions import ExpressionTypeInferer
from .statements import StatementTypeChecker
from ..identity_dict import IdentityDict


class TypeChecker(zuice.Base):
    _declaration_finder = zuice.dependency(name_declaration.DeclarationFinder)
    _name_resolver = zuice.dependency(name_resolution.NameResolver)
    _module_resolver = zuice.dependency(module_resolution.ModuleResolution)
    _module_exports = zuice.dependency(modules.ModuleExports)
    
    def check_module(self, module, module_types):
        # TODO: don't construct the type checker with a module
        module_checker = _TypeCheckerForModule(
            self._declaration_finder,
            self._name_resolver,
            self._module_exports,
            module_types,
            self._module_resolver,
            module,
        )
        module_type = module_checker.check(module)
        return module_type, module_checker.type_lookup()


class _TypeCheckerForModule(object):
    def __init__(self, declaration_finder, name_resolver, module_exports, module_types, module_resolver, module):
        self._declaration_finder = declaration_finder
        self._name_resolver = name_resolver
        self._module_exports = module_exports
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
        references = self._name_resolver.resolve(module.node)
    
        context = builtins.module_context(references)
        for statement in module.node.body:
            self.update_context(statement, context)
        
        for reference in references:
            self._type_lookup[reference] = context.lookup(reference)
        
        module_declarations = self._declaration_finder.declarations_in_module(module.node)
        exported_names = self._module_exports.names(module.node)
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
        


    
