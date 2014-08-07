import os
import shutil

from . import nodejs


def compile(source, nope_ast, destination_dir, platform):
    compilers[platform].compile(source, nope_ast, destination_dir)


class Python2(object):
    name = "python2"
    binary = "python2"
    extension = "py"
    
    def compile(self, source_path, nope_ast, destination_dir):
        def _source_path_to_dest_path(source_full_path):
            if os.path.isfile(source_path):
                root = os.path.dirname(source_path)
            else:
                root = source_path
            relative_path = os.path.relpath(source_full_path, root)
            return os.path.join(destination_dir, relative_path)
        
        def handle_dir(path):
            os.mkdir(_source_path_to_dest_path(path))
        
        def handle_file(path):
            with open(path) as source_file:
                with open(_source_path_to_dest_path(path), "w") as dest_file:
                    started = False
                    while True:
                        line = source_file.readline()
                        
                        if line == "":
                            return
                        
                        if not started and not line.startswith("#"):
                            started = True
                            for future in ["division", "absolute_import", "print_function", "unicode_literals"]:
                                dest_file.write("from __future__ import {}\n".format(future))
                                
                        dest_file.write(line)
        
        _walk_tree(source_path, handle_dir, handle_file)


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
    
    def handle_dir(path):
        os.mkdir(_source_path_to_dest_path(path))
    
    def handle_file(path):
        shutil.copy(path, _source_path_to_dest_path(path))
    
    _walk_tree(source_path, handle_dir, handle_file)


def _walk_tree(path, handle_dir, handle_file):
    if os.path.isdir(path):
        for root, dirnames, filenames in os.walk(path):
            for dirname in dirnames: 
                full_path = os.path.join(root, dirname)
                handle_dir(full_path)
            
            for filename in filenames:
                full_path = os.path.join(root, filename)
                handle_file(full_path)
    else:
        handle_file(path)



_all = [
    Python2(),
    Python3(),
    NodeJs(),
]


compilers = dict((compiler.name, compiler) for compiler in _all)
