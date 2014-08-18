import os

import tempman
import spur

import nope


_local = spur.LocalShell()


def compile_and_run(platform, path, program, allow_error):
    with tempman.create_temp_dir() as temp_dir:
        output_dir = temp_dir.path
        nope.compile(path, output_dir, platform)
        output_path = "{}.{}".format(program, platform.extension)
        return _local.run([platform.binary, output_path], cwd=output_dir, allow_error=allow_error)


def program_path(path):
    return os.path.join(os.path.dirname(__file__), "programs", path)
