import os


def walk_tree(path, handle_dir, handle_file):
    def _source_path_to_relative_path(full_path):
        if os.path.isfile(path):
            root = os.path.dirname(path)
        else:
            root = path
        return os.path.relpath(full_path, root)
        
    if os.path.isdir(path):
        handle_dir(path, _source_path_to_relative_path(path))
        for root, dirnames, filenames in os.walk(path):
            for dirname in dirnames: 
                full_path = os.path.join(root, dirname)
                relative_path = _source_path_to_relative_path(full_path)
                handle_dir(full_path, relative_path)
            
            for filename in filenames:
                full_path = os.path.join(root, filename)
                relative_path = _source_path_to_relative_path(full_path)
                handle_file(full_path, relative_path)
    else:
        handle_file(path, os.path.basename(path))
