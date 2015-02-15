import zuice

from .codegeneration import CodeGenerator


class NodeJs(zuice.Base):
    _code_generator = zuice.dependency(CodeGenerator)
    
    name = "node"
    binary = "node"
    extension = "js"
    
    def generate_code(self, source_path, destination_dir):
        self._code_generator.generate_files(source_path, destination_dir)
