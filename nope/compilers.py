import os
import shutil

from . import nodejs


def compile(source, nope_ast, destination_dir, platform):
    compilers[platform].compile(source, nope_ast, destination_dir)


class Python2(object):
    name = "python2"
    binary = "python2"
    extension = "py"
    
    def compile(self, source, nope_ast, destination_dir):
        _copy_recursive(source, destination_dir)


class Python3(object):
    name = "python3"
    binary = "python3"
    extension = "py"
    
    def compile(self, source, nope_ast, destination_dir):
        _copy_recursive(source, destination_dir)
    

class NodeJs(object):
    name = "node"
    binary = "node"
    extension = "js"
    
    def compile(self, source_path, nope_ast, destination_dir):
        nodejs.nope_to_nodejs(source_path, nope_ast, destination_dir)


def _copy_recursive(source_path, dest_path):
    def _source_path_to_dest_path(source_full_path):
        relative_path = os.path.relpath(source_full_path, source_path)
        return os.path.join(dest_path, relative_path)
    
    if os.path.isdir(source_path):
        for root, dirnames, filenames in os.walk(source_path):
            for dirname in dirnames: 
                full_path = os.path.join(root, dirname)
                os.mkdir(_source_path_to_dest_path(full_path))
            
            for filename in filenames:
                full_path = os.path.join(root, filename)
                _copy_recursive(full_path, _source_path_to_dest_path(full_path))
    else:
        shutil.copy(source_path, dest_path)
    


_all = [
    Python2(),
    Python3(),
    NodeJs(),
]


compilers = dict((compiler.name, compiler) for compiler in _all)
