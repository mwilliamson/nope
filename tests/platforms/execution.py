import os

from nose.tools import istest, nottest, assert_equal
import tempman

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
    
    @istest
    def test_call_int_magic_method_directly(self):
        self._test_expression("(4).__add__(5)", b"9")
    
    @istest
    def test_add_int(self):
        self._test_expression("4 + 5", b"9")
    
    @istest
    def test_sub_int(self):
        self._test_expression("4 - 5", b"-1")
    
    @istest
    def test_mul_int(self):
        self._test_expression("4 * 5", b"20")
    
    @istest
    def test_truediv_int(self):
        self._test_expression("1 / 2", b"0.5")
        self._test_expression("(0 - 1) / 2", b"-0.5")
    
    @istest
    def test_floordiv_int(self):
        self._test_expression("1 // 2", b"0")
        self._test_expression("(0 - 1) // 2", b"-1")
    
    @istest
    def test_mod_int(self):
        self._test_expression("5 % 3", b"2")
        self._test_expression("(0 - 5) % 3", b"1")
    
    @istest
    def test_neg_int(self):
        self._test_expression("-(1 + 2)", b"-3")
    
    @istest
    def test_pos_int(self):
        self._test_expression("+(1 + 2)", b"3")
        self._test_expression("+(0 - 3)", b"-3")
    
    @istest
    def test_abs_int(self):
        self._test_expression("abs(10)", b"10")
        self._test_expression("abs(-12)", b"12")
    
    @istest
    def test_invert_int(self):
        self._test_expression("~10", b"-11")
        self._test_expression("~-10", b"9")
    
    @istest
    def test_getitem_list(self):
        self._test_expression("[42, 53, 75][1]", b"53")
    
    def _test_expression(self, expression, expected_output):
        with tempman.create_temp_dir() as temp_dir:
            with open(os.path.join(temp_dir.path, "main.py"), "w") as main_file:
                main_file.write("#!/usr/bin/env python\n")
                main_file.write("print({})\n".format(expression))
            
            result = self._run_program(path=temp_dir.path, program="main")
        
        assert_equal(0, result.return_code)
        assert_equal(expected_output + b"\n", result.output)
        assert_equal(b"", result.stderr_output)
        
            
    
    def _run_program(self, path, program):
        return testing.compile_and_run(self.platform, path, program)
