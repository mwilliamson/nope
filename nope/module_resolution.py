import os
import collections

import zuice

from . import errors, environment, modules
from .source import SourceTree


ModuleSearchPaths = zuice.key("ModuleSearchPaths")


class ModuleResolverFactory(zuice.Base):
    _injector = zuice.dependency(zuice.Injector)

    def for_module(self, module):
        return self._injector.get(ModuleResolver, {modules.Module: module})


class ModuleResolver(zuice.Base):
    _source_tree = zuice.dependency(SourceTree)
    _builtin_modules = zuice.dependency(environment.BuiltinModules)
    _module_exports = zuice.dependency(modules.ModuleExports)
    _module = zuice.dependency(modules.Module)
    _search_paths = zuice.dependency(ModuleSearchPaths)
    
    def resolve_import_value(self, names, value_name):
        imported_module = self.resolve_import_path(names)
        if value_name is None:
            return ResolvedImport(names, imported_module, None)
        
        # This differs from Python's import semantics in that it favours modules
        # over values in packages with the same name. However, nope's
        # type-checker prevents a package having a value with the same name as
        # a module unless that value *is* the module, making this consistent.
        # Preferring the module allows us to avoid circular dependencies.
        
        try:
            module_names = names + [value_name]
            return ResolvedImport(module_names, self.resolve_import_path(module_names), None)
        except errors.ModuleNotFoundError:
            if self._module_declares_name(imported_module, value_name):
                return ResolvedImport(names, imported_module, value_name)
            else:
                message = "Could not import name '{}' from module '{}'".format(
                    value_name, ".".join(names))
                raise errors.ModuleNotFoundError(None, message)
    
    def _module_declares_name(self, imported_module, name):
        if isinstance(imported_module, modules.BuiltinModule):
            module_names = imported_module.type.attrs.names()
        else:
            module_names = self._module_exports.names(imported_module.node)
        
        return name in module_names
    
    def resolve_import_path(self, names):
        name = ".".join(names)
        if name in self._builtin_modules:
            return self._builtin_modules[name]
        
        module_paths = self._possible_module_paths(self._module.path, names)
        modules = list(filter(None, map(self._source_tree.module, module_paths)))
        
        if len(modules) > 1:
            raise errors.ImportError(None,
                "Import is ambiguous, possible module paths: " +
                    ", ".join("'{}'".format(module.path) for module in modules)
            )
        elif len(modules) == 0:
            raise errors.ModuleNotFoundError(None, "Could not find module '{}'".format(name))
        else:
            module, = modules
            if module.node.is_executable:
                raise errors.ImportError(None, "Cannot import executable modules")
            else:
                return module


    def _possible_module_paths(self, module_path, names):
        if names[0] in [".", ".."] or self._module.node.is_executable:
            yield from self._possible_module_paths_under_search_path(os.path.dirname(module_path), names)
        
        for search_path in self._search_paths:
            yield from self._possible_module_paths_under_search_path(search_path, names)
    
    def _possible_module_paths_under_search_path(self, search_path, names):
        import_path = os.path.normpath(os.path.join(search_path, *names))
        return (
            os.path.join(import_path, "__init__.py"),
            import_path + ".py"
        )


ResolvedImport = collections.namedtuple("ResolvedImport",
    ["module_name", "module", "attr_name"]
)
