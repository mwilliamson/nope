from nose.tools import istest, nottest, assert_equal

from .. import testing
from ..testing import program_path


@nottest
class ExecutionTests(object):
    @istest
    def empty_program_runs_without_output(self):
        result = self._run_program(path=program_path("valid/empty.py"), program="empty")
        assert_equal(0, result.return_code)
        assert_equal(b"", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def print_program_prints_to_stdout(self):
        result = self._run_program(path=program_path("valid/print.py"), program="print")
        assert_equal(0, result.return_code)
        assert_equal(b"42\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def print_def_program_prints_to_stdout(self):
        result = self._run_program(path=program_path("valid/print_def.py"), program="print_def")
        assert_equal(0, result.return_code)
        assert_equal(b"42\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_read_attributes_of_builtins(self):
        result = self._run_program(path=program_path("valid/attribute_read.py"), program="attribute_read")
        assert_equal(0, result.return_code)
        assert_equal(b"1\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_value_from_local_package(self):
        result = self._run_program(path=program_path("valid/import_value_from_local_package"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_local_package(self):
        result = self._run_program(path=program_path("valid/import_local_package"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_local_module(self):
        result = self._run_program(path=program_path("valid/import_local_module"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_module_in_package(self):
        result = self._run_program(path=program_path("valid/import_module_in_package"), program="main")
        assert_equal(0, result.return_code)
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_output_of_bool(self):
        result = self._run_program(path=program_path("valid/bool.py"), program="bool")
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
        result = self._run_program(path=program_path("valid/arithmetic.py"), program="arithmetic")
        assert_equal(0, result.return_code)
        assert_equal(b"19\n1.25\n1\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    def _run_program(self, path, program):
        return testing.compile_and_run(self.platform, path, program)
