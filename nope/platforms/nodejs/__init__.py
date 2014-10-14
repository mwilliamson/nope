import zuice

from . import codegeneration


class NodeJs(zuice.Base):
    _optimise = zuice.argument(default=True)
    
    name = "node"
    binary = "node"
    extension = "js"
    
    def generate_code(self, source_path, source_tree, checker, destination_dir):
        codegeneration.nope_to_nodejs(source_path, source_tree, checker, destination_dir, optimise=self._optimise)
