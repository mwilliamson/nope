import os

from nose.tools import istest, nottest, assert_equal
import spur

import nope
from . import testing


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


@istest
def cannot_import_from_non_existent_package():
    assert not nope.check(path=_program_path("invalid/bad_import")).is_valid


@istest
def cannot_import_from_executable_module():
    assert not nope.check(path=_program_path("invalid/import_executable")).is_valid


@istest
def can_import_from_local_package():
    assert nope.check(path=_program_path("valid/import_value_from_local_package")).is_valid


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
    
    @istest
    def can_read_attributes_of_builtins(self):
        result = self._run_program(path=_program_path("valid/attribute_read.py"), program="attribute_read")
        assert_equal(0, result.return_code)
        assert_equal(b"1\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_value_from_local_package(self):
        result = self._run_program(path=_program_path("valid/import_value_from_local_package"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_local_package(self):
        result = self._run_program(path=_program_path("valid/import_local_package"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_local_module(self):
        result = self._run_program(path=_program_path("valid/import_local_module"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_module_in_package(self):
        result = self._run_program(path=_program_path("valid/import_module_in_package"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_output_of_bool(self):
        result = self._run_program(path=_program_path("valid/bool.py"), program="bool")
        assert_equal(0, result.return_code)
        expected_output = b"""False
True
False
True
False
True
False
True
"""
        assert_equal(expected_output, result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_arithmetic(self):
        result = self._run_program(path=_program_path("valid/arithmetic.py"), program="arithmetic")
        assert_equal(0, result.return_code)
        assert_equal(b"19\n1.25\n1\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    def _run_program(self, path, program):
        return testing.compile_and_run(self.compiler, path, program)


testing.create_platform_test_classes(__name__, ExecutionTests)


def _program_path(path):
    return os.path.join(os.path.dirname(__file__), "programs", path)
