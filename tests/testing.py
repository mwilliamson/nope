import os

import tempman
import spur

import nope


_local = spur.LocalShell()


def compile_and_run(compiler, path, program, allow_error):
    with tempman.create_temp_dir() as temp_dir:
        output_dir = temp_dir.path
        nope.compile(path, output_dir, compiler.name)
        output_path = "{}.{}".format(program, compiler.extension)
        return _local.run([compiler.binary, output_path], cwd=output_dir, allow_error=allow_error)


def program_path(path):
    return os.path.join(os.path.dirname(__file__), "programs", path)
