from . import codegeneration


class NodeJs(object):
    def __init__(self, optimise=True):
        self._optimise = optimise
    
    name = "node"
    binary = "node"
    extension = "js"
    
    def generate_code(self, source_path, source_tree, destination_dir):
        codegeneration.nope_to_nodejs(source_path, source_tree, destination_dir, optimise=self._optimise)
