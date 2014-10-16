from .. import files


class Python3(object):
    name = "python3"
    binary = "python3"
    extension = "py"
    
    def generate_code(self, source, checker, destination_dir):
        files.copy_recursive(source, destination_dir)
