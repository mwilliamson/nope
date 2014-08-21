import os

from nose.tools import istest, nottest, assert_equal, assert_not_equal, assert_in
import tempman

from .. import testing
from ..testing import program_path


# TODO: add tests for with statements (requires class definition support)

@nottest
class ExecutionTests(object):
    @istest
    def empty_program_runs_without_output(self):
        result = self._run_program(path=program_path("valid/empty.py"), program="empty")
        assert_equal(b"", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def print_program_prints_to_stdout(self):
        result = self._run_program(path=program_path("valid/print.py"), program="print")
        assert_equal(b"42\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def print_def_program_prints_to_stdout(self):
        result = self._run_program(path=program_path("valid/print_def.py"), program="print_def")
        assert_equal(b"42\n", result.output)
        assert_equal(b"", result.stderr_output)
        
    @istest
    def fib_program_prints_result_to_stdout(self):
        result = self._run_program(path=program_path("valid/fib.py"), program="fib")
        assert_equal(b"55\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_read_attributes_of_builtins(self):
        result = self._run_program(path=program_path("valid/attribute_read.py"), program="attribute_read")
        assert_equal(b"1\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_value_from_local_package(self):
        result = self._run_program(path=program_path("valid/import_value_from_local_package"), program="main")
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_local_package(self):
        result = self._run_program(path=program_path("valid/import_local_package"), program="main")
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_local_module(self):
        result = self._run_program(path=program_path("valid/import_local_module"), program="main")
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def can_import_module_in_package(self):
        result = self._run_program(path=program_path("valid/import_module_in_package"), program="main")
        assert_equal(b"Hello\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_output_of_bool(self):
        result = self._run_program(path=program_path("valid/bool.py"), program="bool")
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
        self._test_expression("5 % (0 - 3)", b"-1")
        self._test_expression("(0 - 5) % (0 - 3)", b"-2")
    
    @istest
    def test_divmod_int(self):
        self._test_expression("divmod(5, 3)", b"(1, 2)")
        self._test_expression("divmod(-5, 3)", b"(-2, 1)")
        self._test_expression("divmod(5, -3)", b"(-2, -1)")
        self._test_expression("divmod(-5, -3)", b"(1, -2)")
    
    @istest
    def test_pow_int(self):
        self._test_expression("2 ** 3", b"8")
        self._test_expression("2 ** -3", b"0.125")
    
    @istest
    def test_lshift_int(self):
        self._test_expression("5 << 3", b"40")
        self._test_expression("-5 << 3", b"-40")
    
    @istest
    def test_rshift_int(self):
        self._test_expression("41 >> 3", b"5")
        self._test_expression("-41 >> 3", b"-6")
    
    @istest
    def test_bitwise_and_int(self):
        self._test_expression("25 & 51", b"17")
        self._test_expression("-25 & 51", b"35")
    
    @istest
    def test_bitwise_or_int(self):
        self._test_expression("25 | 51", b"59")
        self._test_expression("-25 | 51", b"-9")
    
    @istest
    def test_bitwise_xor_int(self):
        self._test_expression("25 ^ 51", b"42")
        self._test_expression("-25 ^ 51", b"-44")
    
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
    
    @istest
    def test_settitem_list(self):
        self._test_program_string("x = [1]\nx[0] = 2\nprint(x[0])", b"2\n")
    
    @istest
    def test_while(self):
        self._test_program_string("x = 4\nwhile x: x = x - 1\nprint(x)", b"0\n")
    
    @istest
    def test_while_else(self):
        program = """
#:: int -> none
def countdown(length):
    index = length
    while index:
        print(index)
        index = index - 1
    else:
        print("blastoff")

countdown(0)
countdown(1)
countdown(2)

"""
        self._test_program_string(program, b"blastoff\n1\nblastoff\n2\n1\nblastoff\n")
    
    @istest
    def test_while_else_break(self):
        program = """
#:: int -> none
def countdown(length):
    index = length
    while index:
        print(index)
        break
    else:
        print("blastoff")

countdown(0)
countdown(1)
countdown(2)

"""
        self._test_program_string(program, b"blastoff\n1\n2\n")
    
    @istest
    def test_while_else_continue(self):
        program = """
#:: int -> none
def countdown(length):
    index = length
    while index:
        index = index - 1
        continue
        print(index)
    else:
        print("blastoff")

countdown(0)
countdown(1)
countdown(2)

"""
        self._test_program_string(program, b"blastoff\nblastoff\nblastoff\n")
    
    @istest
    def test_for(self):
        self._test_program_string("x = 0\nfor y in [1, 2, 3]:\n  x = x + y\nprint(x)", b"6\n")
    
    @istest
    def test_for_else(self):
        program = """
#:: int -> none
def countup(length):
    for index in range(0, length):
        print(index)
    else:
        print("blastoff")

countup(0)
countup(1)
countup(2)

"""
        self._test_program_string(program, b"blastoff\n0\nblastoff\n0\n1\nblastoff\n")
    
    @istest
    def test_for_else_break(self):
        program = """
#:: int -> none
def countup(length):
    for index in range(0, length):
        print(index)
        break
    else:
        print("blastoff")

countup(0)
countup(1)
countup(2)

"""
        self._test_program_string(program, b"blastoff\n0\n0\n")
    
    @istest
    def test_for_else_continue(self):
        program = """
#:: int -> none
def countup(length):
    for index in range(0, length):
        continue
        print(index)
    else:
        print("blastoff")

countup(0)
countup(1)
countup(2)

"""
        self._test_program_string(program, b"blastoff\nblastoff\nblastoff\n")
    
    @istest
    def test_break_for(self):
        self._test_program_string("y = 0\nfor x in [2, 3]:\n  if y:\n    break\n  y = -x\nprint(y)", b"-2\n")
    
    @istest
    def test_continue_for(self):
        self._test_program_string("y = 1\nfor x in [0, 3]:\n  if x:\n    pass\n  else:\n    continue\n  y = y * x\nprint(y)", b"3\n")
    
    @istest
    def test_unhandled_exception(self):
        result = self._run_program_string("raise Exception('Argh!')", allow_error=True)
        assert_not_equal(0, result.return_code)
        assert_equal(b"", result.output)
        assert_in(b"Exception: Argh!", result.stderr_output)
    
    @istest
    def test_try_except_finally_with_no_exception(self):
        program = """
try:
    print("try")
except:
    print("except")
finally:
    print("finally")
print("done")
        """
        result = self._run_program_string(program)
        assert_equal(b"try\nfinally\ndone\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_try_except_finally_with_exception(self):
        program = """
try:
    print("try-before")
    raise Exception("error")
    print("try-after")
except:
    print("except")
finally:
    print("finally")
print("done")
        """
        result = self._run_program_string(program)
        assert_equal(b"try-before\nexcept\nfinally\ndone\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_try_named_except_finally_with_exception(self):
        program = """
try:
    print("try-before")
    raise Exception("error")
    print("try-after")
except Exception as error:
    print(str(error))
finally:
    print("finally")
print("done")
        """
        result = self._run_program_string(program)
        assert_equal(b"try-before\nerror\nfinally\ndone\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_try_except_with_exception_handles_subexception(self):
        program = """
try:
    print("try-before")
    raise AssertionError("error")
    print("try-after")
except Exception as error:
    print(str(error))
        """
        result = self._run_program_string(program)
        assert_equal(b"try-before\nerror\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_try_except_with_exception_ignores_superexception(self):
        program = """
try:
    print("try-before")
    raise Exception("error")
    print("try-after")
except AssertionError as error:
    print(str(error))
        """
        result = self._run_program_string(program, allow_error=True)
        assert_equal(b"try-before\n", result.output)
        assert_in(b"Exception: error", result.stderr_output)
    
    @istest
    def test_first_matching_exception_handler_runs_first(self):
        program = """
try:
    raise AssertionError("error")
except AssertionError as error:
    print("handling AssertionError")
except Exception as error:
    print("handling Exception")
        """
        result = self._run_program_string(program, allow_error=True)
        assert_equal(b"handling AssertionError\n", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_assert_true_shows_no_output(self):
        result = self._run_program_string("assert True, 'Argh!'")
        assert_equal(b"", result.output)
        assert_equal(b"", result.stderr_output)
    
    @istest
    def test_assert_false_with_message(self):
        result = self._run_program_string("assert False, 'Argh!'", allow_error=True)
        assert_not_equal(0, result.return_code)
        assert_equal(b"", result.output)
        assert_in(b"AssertionError: Argh!", result.stderr_output)
    
    @istest
    def test_assert_false_without_message(self):
        result = self._run_program_string("assert False", allow_error=True)
        assert_not_equal(0, result.return_code)
        assert_equal(b"", result.output)
        assert_in(b"AssertionError", result.stderr_output)
    
    def _test_program_string(self, program, expected_output):
        result = self._run_program_string(program)
        
        assert_equal(expected_output, result.output)
        assert_equal(b"", result.stderr_output)
    
    
    def _run_program_string(self, program, allow_error=False):
        with tempman.create_temp_dir() as temp_dir:
            with open(os.path.join(temp_dir.path, "main.py"), "w") as main_file:
                main_file.write("#!/usr/bin/env python\n")
                main_file.write(program)
            return self._run_program(path=temp_dir.path, program="main", allow_error=allow_error)
        
    
    def _test_expression(self, expression, expected_output):
        self._test_program_string("print({})\n".format(expression), expected_output + b"\n")
        
    
    def _run_program(self, path, program, allow_error=False):
        return testing.compile_and_run(self.platform, path, program, allow_error=allow_error)
