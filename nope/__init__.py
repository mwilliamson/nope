import collections
import os

from . import inference, parser, platforms, errors


def check(path):
    try:
        source_tree = _parse_source_tree(path)
        for path in source_tree.paths():
            source_tree.check(path)
    except (errors.TypeCheckError, SyntaxError) as error:
        return Result(is_valid=False, error=error, value=None)
    
    return Result(is_valid=True, error=None, value=source_tree)


def _parse_source_tree(tree_path):
    def read_ast(path):
        with open(path) as source_file:
            return parser.parse(source_file.read())
    
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


def _check_file(path, source_tree=None):
    with open(path) as source_file:
        source = source_file.read()
        try:
            nope_ast = parser.parse(source)
        except SyntaxError as error:
            return Result(is_valid=False, error=error, value=None)
    
    try:
        inference.check(nope_ast)
    except errors.TypeCheckError as error:
        return Result(is_valid=False, error=error, value=None)
    
    return Result(is_valid=True, error=None, value=nope_ast)


def compile(source_path, destination_dir, platform_name):
    source_tree = check(source_path)
    
    if not source_tree.is_valid:
        raise source_tree.error
    
    platform = platforms.find_platform_by_name(platform_name)
    platform.generate_code(source_path, source_tree.value, destination_dir)


Result = collections.namedtuple("Result", ["is_valid", "error", "value"])


class SourceTree(object):
    def __init__(self, asts):
        self._asts = asts
        self._module_checkers = dict(
            (path, self._checker(ast, path))
            for path, ast in self._asts.items()
        )
    
    def _checker(self, ast, path):
        return lambda: inference.check(ast, self, os.path.abspath(path))
    
    def __contains__(self, value):
        return value in self._asts
    
    def paths(self):
        return self._asts.keys()
    
    def ast(self, path):
        return self._asts[path]
    
    def check(self, path):
        self._type_check_module(path)
    
    def import_module(self, path):
        if path not in self._asts:
            return None
        if self._asts[path].is_executable:
            raise errors.ImportError(None, "Cannot import executable modules")
        return self._type_check_module(path)
        
    def _type_check_module(self, path):
        if path not in self._module_checkers:
            return None
        checker = self._module_checkers[path]
        self._module_checkers[path] = self._circular_import
        result = checker()
        self._module_checkers[path] = lambda: result
        return result
        
        
    
    def _circular_import(self):
        # TODO: test circular import detection
        raise CircularImportError("Circular import detected")


class CircularImportError(Exception):
    pass
