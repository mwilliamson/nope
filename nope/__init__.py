import collections
import os

from . import inference, parser, platforms, errors, loop_control, module_resolution
from .modules import LocalModule


def check(path):
    try:
        source_tree = _parse_source_tree(path)
        checker = Checker(source_tree)
        for module in source_tree.modules():
            checker.check(module)
    except (errors.TypeCheckError, SyntaxError) as error:
        return Result(is_valid=False, error=error, value=None)
    
    return Result(is_valid=True, error=None, value=(source_tree, checker))


def _parse_source_tree(tree_path):
    def read_ast(path):
        with open(path) as source_file:
            return parser.parse(source_file.read(), filename=path)
    
    return SourceTree(dict(
        (path, read_ast(path))
        for path in _source_paths(tree_path)
    ))


def _source_paths(path):
    if os.path.isfile(path):
        yield path
    else:
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                yield os.path.abspath(os.path.join(root, filename))


def compile(source_path, destination_dir, platform):
    result = check(source_path)
    
    if not result.is_valid:
        raise result.error
    
    source_tree, checker = result.value
    
    if isinstance(platform, str):
        platform = platforms.find_platform_by_name(platform)
        
    platform.generate_code(source_path, source_tree, checker, destination_dir)


Result = collections.namedtuple("Result", ["is_valid", "error", "value"])


class Checker(object):
    def __init__(self, source_tree):
        self._source_tree = source_tree
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
        return inference.check(module, module_resolution.ModuleResolution(self._source_tree), self)


class SourceTree(object):
    def __init__(self, asts):
        self._asts = asts
        self._module_checkers = dict(
            (path, self._checker(ast, path))
            for path, ast in self._asts.items()
        )
    
    def _checker(self, ast, path):
        return lambda: _check(ast, self, path)
    
    def __contains__(self, value):
        return value in self._asts
    
    def paths(self):
        return self._asts.keys()
    
    def module(self, path):
        if path in self._asts:
            return LocalModule(path, self._asts[path])
        else:
            return None
    
    def modules(self):
        return [LocalModule(path, node) for path, node in self._asts.items()]


class CircularImportError(Exception):
    pass
