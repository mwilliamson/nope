import os
import shutil

from ..walk import walk_tree


class Python2(object):
    name = "python2"
    binary = "python2"
    extension = "py"
    
    def generate_code(self, source_path, checker, source_tree, destination_dir):
        def handle_dir(path, relative_path):
            os.mkdir(os.path.join(destination_dir, relative_path))
        
        def handle_file(path, relative_path):
            with open(path) as source_file:
                with open(os.path.join(destination_dir, relative_path), "w") as dest_file:
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
        
        walk_tree(source_path, handle_dir, handle_file)


class Python3(object):
    name = "python3"
    binary = "python3"
    extension = "py"
    
    def generate_code(self, source, source_tree, checker, destination_dir):
        _copy_recursive(source, destination_dir)


def _copy_recursive(source_path, dest_path):
    def handle_dir(path, relative_path):
        os.mkdir(os.path.join(dest_path, relative_path))
    
    def handle_file(path, relative_path):
        shutil.copy(path, os.path.join(dest_path, relative_path))
    
    walk_tree(source_path, handle_dir, handle_file)
