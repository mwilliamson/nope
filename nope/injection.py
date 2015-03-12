import zuice

from .name_declaration import DeclarationFinder
from .check import ModuleChecker
from .source import SourceTree, CachedSourceTree, TransformingSourceTree, FileSystemSourceTree
from . import environment, builtins, inference, types, transformers
from .modules import Module
from .desugar import Desugarrer
from .module_resolution import ModuleSearchPaths


def create_bindings():
    # TODO: set default lifetime of singleton
    
    declaration_finder = DeclarationFinder()
    
    bindings = zuice.Bindings()
    bindings.bind(DeclarationFinder).to_instance(declaration_finder)
    bindings.bind(SourceTree).to_provider(_source_tree_provider)
    bindings.bind(environment.Builtins).to_instance(builtins)
    bindings.bind(environment.InitialDeclarations).to_provider(lambda injector:
        injector.get(environment.Builtins).declarations()
    )
    bindings.bind(environment.BuiltinModules).to_provider(lambda injector:
        injector.get(environment.Builtins).builtin_modules
    )
    bindings.bind(ModuleChecker).to_provider(lambda injector:
        ModuleChecker(injector.get(SourceTree), injector.get(inference.TypeChecker))
    )
    bindings.bind(types.TypeLookup).to_provider(_type_lookup_provider)
    bindings.bind(ModuleSearchPaths).to_instance([])
    
    return bindings


def _type_lookup_provider(injector):
    return injector.get(ModuleChecker).type_lookup(injector.get(Module))


def create_injector():
    bindings = create_bindings()
    return zuice.Injector(bindings)


def _source_tree_provider(injector):
    return CachedSourceTree(
        TransformingSourceTree(
            TransformingSourceTree(
                FileSystemSourceTree(),
                create_injector().get(transformers.ClassBuilderTransform, {
                    transformers.ModuleName: "collections",
                    transformers.FuncName: "namedtuple",
                })
            ),
            create_injector().get(transformers.ClassBuilderTransform, {
                transformers.ModuleName: "dodge",
                transformers.FuncName: "data_class",
            })
        )
    )


class CouscousTree(zuice.Base):
    _source_tree = zuice.dependency(SourceTree)
    _desugarrer_factory = zuice.dependency(zuice.factory(Desugarrer))
    
    def module(self, path):
        module = self._source_tree.module(path)
        if module is None:
            return None
        else:
            desugarrer = self._desugarrer_factory({Module: module})
            return desugarrer.desugar(module)
