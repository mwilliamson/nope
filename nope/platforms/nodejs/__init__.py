from . import codegeneration


class NodeJs(object):
    name = "node"
    binary = "node"
    extension = "js"
    
    def compile(self, source_path, nope_ast, destination_dir):
        codegeneration.nope_to_nodejs(source_path, nope_ast, destination_dir)
