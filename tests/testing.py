import os
import contextlib

import tempman

import nope


@contextlib.contextmanager
def compiled(platform, path, program):
    with tempman.create_temp_dir() as temp_dir:
        output_dir = temp_dir.path
        nope.compile(path, output_dir, platform)
        filename = "{}.{}".format(program, platform.extension)
        yield CompiledCode(output_dir, filename)


class CompiledCode(object):
    def __init__(self, cwd, main):
        self.cwd = cwd
        self.main = main


def program_path(path):
    return os.path.join(os.path.dirname(__file__), "programs", path)
