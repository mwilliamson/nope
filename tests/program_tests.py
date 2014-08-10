from nose.tools import istest
import spur

import nope
from .testing import program_path


_local = spur.LocalShell()


@istest
def empty_program_is_valid():
    assert nope.check(path=program_path("valid/empty.py")).is_valid


@istest
def print_program_is_valid():
    assert nope.check(path=program_path("valid/print.py")).is_valid


# TODO:
@istest
def fib_program_is_valid():
    print(nope.check(path=program_path("valid/fib.py")))
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
    assert nope.check(path=program_path("valid/call_comment_signature.py")).is_valid


@istest
def cannot_import_from_non_existent_package():
    assert not nope.check(path=program_path("invalid/bad_import")).is_valid


@istest
def cannot_import_from_executable_module():
    assert not nope.check(path=program_path("invalid/import_executable")).is_valid


@istest
def can_import_from_local_package():
    assert nope.check(path=program_path("valid/import_value_from_local_package")).is_valid
