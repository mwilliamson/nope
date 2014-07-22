import os

from nose.tools import istest, nottest, assert_equal
import tempman
import spur

import nope


_local = spur.LocalShell()


@istest
def empty_program_is_valid():
    assert nope.check(path=_program_path("valid/empty.py")).is_valid


@istest
def print_program_is_valid():
    assert nope.check(path=_program_path("valid/print.py")).is_valid


# TODO:
#~ @istest
def fib_program_is_valid():
    assert nope.check(path=_program_path("valid/fib.py")).is_valid


@istest
def invalid_syntax_is_invalid_program():
    assert not nope.check(path=_program_path("invalid/invalid_syntax.py")).is_valid


@istest
def calling_function_with_wrong_type_is_invalid():
    assert not nope.check(path=_program_path("invalid/wrong_arg_type.py")).is_valid


@istest
def calling_function_with_correct_type_is_valid():
    assert nope.check(path=_program_path("valid/call.py")).is_valid
    assert nope.check(path=_program_path("valid/call_comment_signature.py")).is_valid


@nottest
class ExecutionTests(object):
    @istest
    def empty_program_runs_without_output(self):
        result = self.run_program(path=_program_path("valid/empty.py"), program="empty.py")
        assert_equal(0, result.return_code)
        assert_equal(b"", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def print_program_prints_to_stdout(self):
        result = self.run_program(path=_program_path("valid/print.py"), program="print.py")
        assert_equal(0, result.return_code)
        assert_equal(b"42\n", result.output)
        assert_equal(b"", result.stderr_output)


@istest
class Python3ExecutionTests(ExecutionTests):
    def run_program(self, path, program):
        with tempman.create_temp_dir() as temp_dir:
            output_dir = temp_dir.path
            nope.compile(path, output_dir, "python3")
            return _local.run(["python3", program], cwd=output_dir)


@istest
class Python2ExecutionTests(ExecutionTests):
    def run_program(self, path, program):
        with tempman.create_temp_dir() as temp_dir:
            output_dir = temp_dir.path
            nope.compile(path, output_dir, "python2")
            return _local.run(["python2", program], cwd=output_dir)


def _program_path(path):
    return os.path.join(os.path.dirname(__file__), "programs", path)
