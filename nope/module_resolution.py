import os
import collections

import zuice

from . import errors, injection, modules
from .identity_dict import IdentityDict


class ModuleResolverFactory(zuice.Base):
    _injector = zuice.dependency(zuice.Injector)

    def for_module(self, module):
        return self._injector.get(ModuleResolver, module=module)


class ModuleResolver(zuice.Base):
    _source_tree = zuice.dependency(injection.source_tree)
    _builtin_modules = zuice.dependency(injection.builtin_modules)
    _module_exports = zuice.dependency(modules.ModuleExports)
    _module = zuice.argument()
    
    def resolve_import_value(self, names, value_name):
        imported_module = self.resolve_import_path(names)
        if value_name is None:
            return ResolvedImport(imported_module, None)
        else:
            if isinstance(imported_module, modules.BuiltinModule):
                module_names = imported_module.type.attrs.names()
            else:
                module_names = self._module_exports.names(imported_module.node)
            if value_name in module_names:
                return ResolvedImport(imported_module, value_name)
            else:
                return self.resolve_import_path(names + [value_name]), None
    
    def resolve_import_path(self, names):
        name = ".".join(names)
        if name in self._builtin_modules:
            return self._builtin_modules[name]
        
        if names[0] not in [".", ".."] and not self._module.node.is_executable:
            package_value, module_value = None, None
        else:
            package_path, module_path = self._possible_module_paths(self._module.path, names)
            
            package_value = self._source_tree.module(package_path)
            module_value = self._source_tree.module(module_path)
        
        if package_value is not None and module_value is not None:
            raise errors.ImportError(None,
                "Import is ambiguous: the module '{0}.py' and the package '{0}/__init__.py' both exist".format(
                    names[-1])
            )
        elif package_value is None and module_value is None:
            raise errors.ModuleNotFoundError(None, "Could not find module '{}'".format(name))
        else:
            module = package_value or module_value
            if module.node.is_executable:
                raise errors.ImportError(None, "Cannot import executable modules")
            else:
                return module


    def _possible_module_paths(self, module_path, names):
        import_path = os.path.normpath(os.path.join(os.path.dirname(module_path), *names))
        
        return (
            os.path.join(import_path, "__init__.py"),
            import_path + ".py"
        )


ResolvedImport = collections.namedtuple("ResolvedImport",
    ["module", "attr_name"]
)
