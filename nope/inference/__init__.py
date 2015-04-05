import zuice

from .. import types, name_declaration, name_resolution, name_binding, builtins, module_resolution, modules
from .expressions import ExpressionTypeInferer
from .statements import StatementTypeChecker
from ..identity_dict import NodeDict
from .context import Context


class TypeChecker(zuice.Base):
    _injector = zuice.dependency(zuice.Injector)
    
    def check_module(self, module, module_types):
        module_checker = self._injector.get(_TypeCheckerForModule, {
            modules.Module: module,
            modules.ModuleTypes: module_types,
        })
        return module_checker.check()


class _TypeCheckerForModule(zuice.Base):
    _declaration_finder = zuice.dependency(name_declaration.DeclarationFinder)
    _name_resolver = zuice.dependency(name_resolution.NameResolver)
    _module_resolver = zuice.dependency(module_resolution.ModuleResolver)
    _module_exports = zuice.dependency(modules.ModuleExports)
    _module = zuice.dependency(modules.Module)
    _module_types = zuice.dependency(modules.ModuleTypes)
    
    @zuice.init
    def init(self):
        self._type_lookup = NodeDict()
        self._expression_type_inferer = ExpressionTypeInferer(self._type_lookup)
        self._statement_type_checker = StatementTypeChecker(
            self._declaration_finder,
            self._expression_type_inferer,
            self._module_resolver,
            self._module_types,
            self._module
        )
    
    def type_lookup(self):
        return types.TypeLookup(self._type_lookup)
    
    def infer(self, expression, context, hint=None):
        return self._expression_type_inferer.infer(expression, context, hint=hint)

    def update_context(self, statement, context):
        self._statement_type_checker.update_context(statement, context)

    def check(self):
        module = self._module
        references = self._name_resolver.resolve(module.node)
    
        context = module_context(references)
        self.update_context(module.node.body, context)
        context.update_deferred()
        
        for reference in references:
            self._type_lookup[reference] = context.lookup(reference)
        
        exported_declarations = self._module_exports.declarations(module.node)
        
        builtin_is_definitely_bound = builtins.module_bindings(references)
        bindings = name_binding.check_bindings(
            module.node,
            references=references,
            type_lookup=self.type_lookup(),
            is_definitely_bound=builtin_is_definitely_bound,
        )
        
        module_type = types.module(module.path, [
            # TODO: set read_only as appropriate
            types.attr(declaration.name, context.lookup_declaration(declaration))
            for declaration in exported_declarations
            if bindings.is_declaration_definitely_bound(declaration)
        ])
        
        self._type_lookup[module.node] = module_type
        
        return module_type, self.type_lookup()
        

def module_context(references):
    return Context(references, builtins.builtin_declaration_types, NodeDict()).enter_module()
