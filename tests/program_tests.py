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
        result = self._run_program(path=_program_path("valid/empty.py"), program="empty")
        assert_equal(0, result.return_code)
        assert_equal(b"", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def print_program_prints_to_stdout(self):
        result = self._run_program(path=_program_path("valid/print.py"), program="print")
        assert_equal(0, result.return_code)
        assert_equal(b"42\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def print_def_program_prints_to_stdout(self):
        result = self._run_program(path=_program_path("valid/print_def.py"), program="print_def")
        assert_equal(0, result.return_code)
        assert_equal(b"42\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    def _run_program(self, path, program):
        with tempman.create_temp_dir() as temp_dir:
            output_dir = temp_dir.path
            nope.compile(path, output_dir, self.platform)
            output_path = "{}.{}".format(program, self.extension)
            return _local.run([self.binary, output_path], cwd=output_dir)


@istest
class Python3ExecutionTests(ExecutionTests):
    platform = "python3"
    binary = "python3"
    extension = "py"


@istest
class Python2ExecutionTests(ExecutionTests):
    platform = "python2"
    binary = "python2"
    extension = "py"


@istest
class NodeExecutionTests(ExecutionTests):
    platform = "node"
    binary = "node"
    extension = "js"


def _program_path(path):
    return os.path.join(os.path.dirname(__file__), "programs", path)
