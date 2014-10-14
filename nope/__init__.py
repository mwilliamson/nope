import collections
import os

import zuice

from . import inference, parser, platforms, errors, loop_control, module_resolution, injection, builtins
from .modules import LocalModule
from .transformers import CollectionsNamedTupleTransform
from .name_declaration import DeclarationFinder
from .name_resolution import NameResolver


def check(path):
    checker = _injector().get(SourceChecker)
    return checker.check(path)


def compile(source_path, destination_dir, platform):
    compiler = _injector().get(Compiler)
    return compiler.compile(source_path, destination_dir, platform)


def _injector():
    # TODO: set default lifetime of singleton
    
    declaration_finder = DeclarationFinder()
    
    bindings = zuice.Bindings()
    bindings.bind(DeclarationFinder).to_instance(declaration_finder)
    bindings.bind(injection.source_tree).to_provider(_source_tree_provider)
    bindings.bind(injection.builtins).to_instance(builtins)
    bindings.bind(injection.initial_declarations).to_provider(lambda injector:
        injector.get(injection.builtins).declarations()
    )
    bindings.bind(injection.builtin_modules).to_provider(lambda injector:
        injector.get(injection.builtins).builtin_modules
    )
    bindings.bind(ModuleChecker).to_provider(lambda injector:
        ModuleChecker(injector.get(injection.source_tree), injector.get(inference.TypeChecker))
    )
    
    return zuice.Injector(bindings)


def _source_tree_provider(injector):
    return CachedSourceTree(
        TransformingSourceTree(
            SourceTree(),
            _injector().get(CollectionsNamedTupleTransform)
        )
    )


def _source_paths(path):
    if os.path.isfile(path):
        yield path
    else:
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                yield os.path.abspath(os.path.join(root, filename))


class ModuleChecker(object):
    def __init__(self, source_tree, type_checker):
        self._source_tree = source_tree
        self._type_checker = type_checker
        self._check_results = {}
    
    def check(self, module):
        self._check_result(module)
    
    def _check_result(self, module):
        # TODO: circular import detection
        if module not in self._check_results:
            self._check_results[module] = self._uncached_check(module)
        return self._check_results[module]
    
    def type_of_module(self, module):
        module_type, type_lookup = self._check_result(module)
        return module_type
    
    def type_lookup(self, module):
        module_type, type_lookup = self._check_result(module) 
        return type_lookup
    
    def _uncached_check(self, module):
        loop_control.check_loop_control(module.node, in_loop=False)
        return self._type_checker.check_module(module, self)


class SourceChecker(zuice.Base):
    _source_tree = zuice.dependency(injection.source_tree)
    _module_checker = zuice.dependency(ModuleChecker)
    
    def check(self, path):
        try:
            for source_path in _source_paths(path):
                module = self._source_tree.module(source_path)
                self._module_checker.check(module)
        except (errors.TypeCheckError, SyntaxError) as error:
            return Result(is_valid=False, error=error, value=None)
        
        return Result(is_valid=True, error=None, value=(self._source_tree, self._module_checker))


class Compiler(zuice.Base):
    _checker = zuice.dependency(SourceChecker)
    _injector = zuice.dependency(zuice.Injector)
    
    def compile(self, source_path, destination_dir, platform):
        result = self._checker.check(source_path)
        
        if not result.is_valid:
            raise result.error
        
        source_tree, checker = result.value
        
        if isinstance(platform, str):
            platform = self._injector.get(platforms.find_platform_by_name(platform))
            
        platform.generate_code(source_path, source_tree, checker, destination_dir)
        


Result = collections.namedtuple("Result", ["is_valid", "error", "value"])


class CachedSourceTree(object):
    def __init__(self, source_tree):
        self._asts = {}
        self._source_tree = source_tree
    
    def module(self, path):
        if path not in self._asts:
            self._asts[path] = self._source_tree.module(path)
        
        return self._asts[path]


class TransformingSourceTree(object):
    def __init__(self, source_tree, transform):
        self._source_tree = source_tree
        self._transform = transform
    
    def module(self, path):
        module = self._source_tree.module(path)
        if module is None:
            return None
        else:
            return LocalModule(module.path, self._transform(module.node))


class SourceTree(object):
    def module(self, path):
        if not os.path.exists(path) or not os.path.isfile(path):
            return None
                
        with open(path) as source_file:
            module_node = parser.parse(source_file.read(), filename=path)
            return LocalModule(path, module_node)


class CircularImportError(Exception):
    pass
