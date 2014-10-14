import zuice

from .name_declaration import DeclarationFinder
from .check import ModuleChecker
from .source import CachedSourceTree, TransformingSourceTree, SourceTree
from .transformers import CollectionsNamedTupleTransform
from . import deps, builtins, inference


def create_bindings():
    # TODO: set default lifetime of singleton
    
    declaration_finder = DeclarationFinder()
    
    bindings = zuice.Bindings()
    bindings.bind(DeclarationFinder).to_instance(declaration_finder)
    bindings.bind(deps.source_tree).to_provider(_source_tree_provider)
    bindings.bind(deps.builtins).to_instance(builtins)
    bindings.bind(deps.initial_declarations).to_provider(lambda injector:
        injector.get(deps.builtins).declarations()
    )
    bindings.bind(deps.builtin_modules).to_provider(lambda injector:
        injector.get(deps.builtins).builtin_modules
    )
    bindings.bind(ModuleChecker).to_provider(lambda injector:
        ModuleChecker(injector.get(deps.source_tree), injector.get(inference.TypeChecker))
    )
    return bindings


def create_injector():
    bindings = create_bindings()
    return zuice.Injector(bindings)


def _source_tree_provider(injector):
    return CachedSourceTree(
        TransformingSourceTree(
            SourceTree(),
            create_injector().get(CollectionsNamedTupleTransform)
        )
    )
