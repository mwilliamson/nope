import os
import contextlib
import functools

import tempman
from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest

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


def wip(func):
    @functools.wraps(func)
    def run_test(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            raise SkipTest("WIP test failed: " + str(e))
        assert False, "test passed but marked as work in progress"
    return attr('wip')(run_test)


def assert_raises(error_type, func):
    try:
        func()
        assert False, "Expected '{}' to be raised".format(error_type.__name__)
    except error_type as error:
        return error
