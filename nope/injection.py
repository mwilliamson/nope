import zuice

from .name_declaration import DeclarationFinder
from .check import ModuleChecker, SourceChecker
from .source import SourceTree, CachedSourceTree, TransformingSourceTree, FileSystemSourceTree
from .transformers import CollectionsNamedTupleTransform
from . import environment, builtins, inference, types


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
    bindings.bind(types.TypeLookupFactory).to_provider(_provide_type_lookup_factory)
    return bindings


def _provide_type_lookup_factory(injector):
    return SourceCheckerToTypeLookupFactoryAdaptor(injector.get(ModuleChecker))


# Eurgh!
class SourceCheckerToTypeLookupFactoryAdaptor(object):
    def __init__(self, module_checker):
        self._module_checker = module_checker
    
    def for_module(self, module):
        return self._module_checker.type_lookup(module)


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
