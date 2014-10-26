import os

from nose.tools import istest, assert_equal
import spur
import tempman


_local = spur.LocalShell()


@istest
def cli_can_compile_programs_to_node_js():
    with tempman.create_temp_dir() as temp_dir:
        output_dir = os.path.join(temp_dir.path, "output")
        os.mkdir(output_dir)
        
        path = os.path.join(temp_dir.path, "main.py")
        with open(path, "w") as main_file:
            main_file.write("#!/usr/bin/env python\n")
            main_file.write("print('Hello')")
        
        _local.run([
            "nope", "compile", path,
            "--backend=node",
            "--output-dir", output_dir
        ])
        
        result = _local.run(["node", os.path.join(output_dir, "main.js")])
        assert_equal(b"Hello\n", result.output)
