import os

from nose.tools import istest, assert_equal
import spur
import tempman

import nope
from .testing import program_path


_local = spur.LocalShell()


@istest
def empty_program_is_valid():
    assert nope.check(path=program_path("valid/empty.py")).is_valid


@istest
def print_program_is_valid():
    assert nope.check(path=program_path("valid/print.py")).is_valid


@istest
def fib_program_is_valid():
    assert nope.check(path=program_path("valid/fib.py")).is_valid


@istest
def invalid_syntax_is_invalid_program():
    assert not nope.check(path=program_path("invalid/invalid_syntax.py")).is_valid


@istest
def calling_function_with_wrong_type_is_invalid():
    assert not nope.check(path=program_path("invalid/wrong_arg_type.py")).is_valid


@istest
def calling_function_with_correct_type_is_valid():
    assert nope.check(path=program_path("valid/call.py")).is_valid


@istest
def cannot_import_from_non_existent_package():
    assert not nope.check(path=program_path("invalid/bad_import")).is_valid


@istest
def cannot_import_from_executable_module():
    assert not nope.check(path=program_path("invalid/import_executable")).is_valid


@istest
def can_import_from_local_package():
    assert nope.check(path=program_path("valid/import_value_from_local_package")).is_valid


@istest
def test_loop_control_module_is_run():
    result = _check_program_string("break")
    assert not result.is_valid
    assert_equal("'break' outside loop", str(result.error))
        

def _check_program_string(program):
    with tempman.create_temp_dir() as temp_dir:
        path = os.path.join(temp_dir.path, "main.py")
        with open(path, "w") as main_file:
            main_file.write("#!/usr/bin/env python\n")
            main_file.write(program)
        return nope.check(path=path)
    
