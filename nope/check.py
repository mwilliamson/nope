import collections

import zuice

from . import loop_control, errors, paths
from .source import SourceTree


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
    _source_tree = zuice.dependency(SourceTree)
    _module_checker = zuice.dependency(ModuleChecker)
    
    def check(self, path):
        if isinstance(path, str):
            roots = [path]
        else:
            roots = path
        
        try:
            for source_path in _source_paths(roots):
                module = self._source_tree.module(source_path)
                self._module_checker.check(module)
        except (errors.TypeCheckError, SyntaxError) as error:
            return Result(is_valid=False, error=error, value=None)
        
        return Result(is_valid=True, error=None, value=None)
        

Result = collections.namedtuple("Result", ["is_valid", "error", "value"])


def _source_paths(roots):
    return set(
        path
        for root in roots
        for path in paths.find_files(root)
    )
