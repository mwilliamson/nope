from . import codegeneration


class NodeJs(object):
    name = "node"
    binary = "node"
    extension = "js"
    
    def generate_code(self, source_path, source_tree, destination_dir):
        codegeneration.nope_to_nodejs(source_path, source_tree, destination_dir)
