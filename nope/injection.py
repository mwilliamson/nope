import zuice

from .name_declaration import DeclarationFinder
from .check import ModuleChecker, SourceChecker
from .source import SourceTree, CachedSourceTree, TransformingSourceTree, FileSystemSourceTree
from .transformers import CollectionsNamedTupleTransform
from . import environment, builtins, inference, types
from .modules import Module


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
    return bindings


def _type_lookup_provider(injector):
    return injector.get(ModuleChecker).type_lookup(injector.get(Module))


def create_injector():
    bindings = create_bindings()
    return zuice.Injector(bindings)


def _source_tree_provider(injector):
    return CachedSourceTree(
        TransformingSourceTree(
            FileSystemSourceTree(),
            create_injector().get(CollectionsNamedTupleTransform)
        )
    )
