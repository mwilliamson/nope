import os
import inspect
import shutil

import zuice

from ...source import SourceTree
from ... import files
from ...modules import Module
from ...walk import walk_tree


class CodeGenerator(zuice.Base):
    _source_tree = zuice.dependency(SourceTree)
    
    def generate_files(self, source_path, destination_root):
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_root, relative_path))
        
        def handle_file(path, relative_path):
            module = self._source_tree.module(path)
            
            destination_dir = os.path.dirname(os.path.join(destination_root, relative_path))
            
            source_filename = os.path.basename(path)
            dest_filename = _js_filename(source_filename)
            dest_path = os.path.join(destination_dir, dest_filename)
            with open(dest_path, "w") as dest_file:
                _generate_prelude(dest_file, module.node.is_executable, relative_path)
                node_transformer = self._node_transformer_factory({Module: module})
                js.dump(node_transformer.transform(module.node), dest_file)
        
        _write_nope_js(destination_root)
        _write_builtins(destination_root)
        
        walk_tree(source_path, handle_dir, handle_file)


class CodeGenerator(zuice.Base):
    def generate_files(self, source_path, destination_dir):
        pass
