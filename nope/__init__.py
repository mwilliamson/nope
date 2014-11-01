import zuice

from . import platforms, errors, injection
from .check import SourceChecker
from .platforms import nodejs
from .source import SourceTree


def check(path):
    return checker.check(path)

def compile(source_path, destination_dir, platform):
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
            # TODO: remove explicit mention of nodejs. Introduce default bindings to platforms?
            platform = self._injector.get(platform_class, {nodejs.optimise: True})
            
        platform.generate_code(source_path, destination_dir)


checker = injection.injector.get(SourceChecker)
compiler = injection.injector.get(Compiler)
