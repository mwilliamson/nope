import os
import shutil

from ..walk import walk_tree


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
