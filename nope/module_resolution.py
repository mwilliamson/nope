import os

from . import errors
from .identity_dict import IdentityDict


class ModuleResolution(object):
    def __init__(self, source_tree, builtin_modules):
        self._source_tree = source_tree
        self._builtin_modules = builtin_modules
    
    def resolve_import(self, module, names):
        name = ".".join(names)
        if name in self._builtin_modules:
            return self._builtin_modules[name]
        
        if names[0] not in [".", ".."] and not module.node.is_executable:
            package_value, module_value = None, None
        else:
            package_path, module_path = self._possible_module_paths(module.path, names)
            
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


class ResolvedImports(object):
    def __init__(self, imports):
        self._imports = imports

    def referenced_module(self, import_alias):
        return self._imports[import_alias]
