import os

import zuice

from . import parser
from .modules import LocalModule


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


class FileSystemSourceTree(object):
    def module(self, path):
        if not os.path.exists(path) or not os.path.isfile(path):
            return None
                
        with open(path) as source_file:
            module_node = parser.parse(source_file.read(), filename=path)
            return LocalModule(path, module_node)


class CircularImportError(Exception):
    pass


SourceTree = zuice.key("SourceTree")
