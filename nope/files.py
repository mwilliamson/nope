import os
import shutil

from .walk import walk_tree


def copy_recursive(source_path, dest_path):
    def handle_dir(path, relative_path):
        mkdir_p(os.path.join(dest_path, relative_path))
    
    def handle_file(path, relative_path):
        shutil.copy(path, os.path.join(dest_path, relative_path))
    
    walk_tree(source_path, handle_dir, handle_file)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def replace_extension(filename, new_extension):
    return filename[:filename.rindex(".")] + "." + new_extension
