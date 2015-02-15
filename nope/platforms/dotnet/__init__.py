import zuice

from .codegeneration import CodeGenerator


class DotNet(zuice.Base):
    _code_generator = zuice.dependency(CodeGenerator)
    
    name = "dotnet"
    binary = "mono"
    extension = "exe"
    
    def generate_code(self, source_path, destination_dir):
        self._code_generator.generate_files(source_path, destination_dir)

