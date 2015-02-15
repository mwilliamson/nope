import zuice

from . import platforms, injection
from .check import SourceChecker


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
        
        if isinstance(platform, str):
            platform_class = platforms.find_platform_by_name(platform)
            platform = self._injector.get(platform_class)
            
        platform.generate_code(source_path, destination_dir)
