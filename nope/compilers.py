import os
import shutil

from . import nodejs


def compile(source, nope_ast, destination_dir, platform):
    _compilers[platform](source, nope_ast, destination_dir)


def python2(source, nope_ast, destination_dir):
    _copy_recursive(source, destination_dir)


def python3(source, nope_ast, destination_dir):
    _copy_recursive(source, destination_dir)


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
    


def node(source_path, nope_ast, destination_dir):
    nodejs.nope_to_nodejs(source_path, nope_ast, destination_dir)


_compilers = {
    "python2": python2,
    "python3": python3,
    "node": node,
}
