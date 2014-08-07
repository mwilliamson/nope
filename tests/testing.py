import sys

import tempman
import spur
from nose.tools import istest, nottest

import nope
from nope import platforms


_local = spur.LocalShell()


def compile_and_run(compiler, path, program):
    with tempman.create_temp_dir() as temp_dir:
        output_dir = temp_dir.path
        nope.compile(path, output_dir, compiler.name)
        output_path = "{}.{}".format(program, compiler.extension)
        return _local.run([compiler.binary, output_path], cwd=output_dir)


def _create_test_class(test_base, compiler):
    @istest
    class PlatformExecutionTests(test_base):
        pass
    
    PlatformExecutionTests.__name__ = "{}{}".format(type(compiler).__name__, test_base.__name__)
    PlatformExecutionTests.compiler = compiler
    return PlatformExecutionTests


@nottest
def create_platform_test_classes(module_name, test_base):
    module = sys.modules[module_name]
    for compiler in platforms.platforms.values():
        test_class = _create_test_class(test_base, compiler)
        setattr(module, test_class.__name__, test_class)

