import collections
import os

from . import inference, parser, compilers


def check(path):
    if os.path.isdir(path):
        return _check_dir(path)
    else:
        return _check_file(path)


def _check_dir(path):
    source_tree = _parse_source_tree(path)
    
    try:
        for path in source_tree.paths():
            source_tree.check(path)
    except inference.TypeCheckError as error:
        return Result(is_valid=False, error=error, value=None)
    
    return Result(is_valid=True, error=None, value=source_tree)


def _parse_source_tree(tree_path):
    def read_ast(path):
        with open(path) as source_file:
            return parser.parse(source_file.read())
    
    try:
        return SourceTree(dict(
            (path, read_ast(path))
            for path in _source_paths(tree_path)
        ))
    except SyntaxError as error:
        return Result(is_valid=False, error=error, value=None)


def _source_paths(path):
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
    except inference.TypeCheckError as error:
        return Result(is_valid=False, error=error, value=None)
    
    return Result(is_valid=True, error=None, value=nope_ast)


def compile(source, destination_dir, platform):
    nope_ast = check(source)
    
    if not nope_ast.is_valid:
        raise nope_ast.error
    
    compilers.compile(source, nope_ast.value, destination_dir, platform)


Result = collections.namedtuple("Result", ["is_valid", "error", "value"])


class SourceTree(object):
    def __init__(self, asts):
        self._asts = asts
        self._module_checkers = dict(
            (path, self._checker(ast, path))
            for path, ast in self._asts.items()
        )
    
    def _checker(self, ast, path):
        return lambda: inference.check(ast, self, path)
    
    def paths(self):
        return self._asts.keys()
    
    def check(self, path):
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
