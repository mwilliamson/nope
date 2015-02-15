import os
import subprocess

import zuice

from ... import files
from ...walk import walk_tree


class CodeGenerator(zuice.Base):
    def generate_files(self, source_path, destination_root):
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_root, relative_path))
        
        def handle_file(path, relative_path):
            dest_cs_filename = files.replace_extension(
                os.path.join(destination_root, relative_path),
                "cs"
            )
            dest_exe_filename = files.replace_extension(dest_cs_filename, "exe")
            
            with open(dest_cs_filename, "w") as dest_cs_file:
                dest_cs_file.write("""
internal class Program
{
    internal static void Main()
    {
    }
}
""")
            subprocess.check_call(["mcs", dest_cs_filename, "-out:{}".format(dest_exe_filename)])
        
        walk_tree(source_path, handle_dir, handle_file)
