import collections
import os

import zuice

from . import platforms, errors, injection, deps
from .check import ModuleChecker
from .platforms import nodejs
from .source import SourceTree


def check(path):
    checker = injection.create_injector().get(SourceChecker)
    return checker.check(path)


def compile(source_path, destination_dir, platform):
    compiler = injection.create_injector().get(Compiler)
    return compiler.compile(source_path, destination_dir, platform)


def _source_paths(path):
    if os.path.isfile(path):
        yield path
    else:
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                yield os.path.abspath(os.path.join(root, filename))


class SourceChecker(zuice.Base):
    _source_tree = zuice.dependency(SourceTree)
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
            # TODO: support proper injector extension in zuice
            platform_bindings = self._injector._bindings.copy()
            # TODO: remove this ugly hack. Introduce default bindings to platforms?
            platform_bindings.bind(nodejs.optimise).to_instance(True)
            platform_injector = zuice.Injector(platform_bindings)
            
            platform = platform_injector.get(platforms.find_platform_by_name(platform))
            
        platform.generate_code(source_path, source_tree, checker, destination_dir)
        


Result = collections.namedtuple("Result", ["is_valid", "error", "value"])
