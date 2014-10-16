import zuice

from . import platforms, errors, injection
from .check import SourceChecker
from .platforms import nodejs
from .source import SourceTree


def check(path):
    checker = injection.create_injector().get(SourceChecker)
    return checker.check(path)


def compile(source_path, destination_dir, platform):
    compiler = injection.create_injector().get(Compiler)
    return compiler.compile(source_path, destination_dir, platform)


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
            
        platform.generate_code(source_path, destination_dir)
