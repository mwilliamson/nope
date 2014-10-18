import zuice

from . import codegeneration


optimise = zuice.key("optimise")


class NodeJs(zuice.Base):
    _optimise = zuice.dependency(optimise)
    _code_generator = zuice.dependency(codegeneration.CodeGenerator)
    
    name = "node"
    binary = "node"
    extension = "js"
    
    def generate_code(self, source_path, destination_dir):
        self._code_generator.generate_files(source_path, destination_dir, optimise=self._optimise)
