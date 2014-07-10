import os

from nose.tools import istest, assert_equal

import nope


@istest
def empty_program_is_valid():
    assert nope.check(path=_program_path("valid/empty.py")).is_valid


@istest
def invalid_syntax_is_invalid_program():
    assert not nope.check(path=_program_path("invalid/invalid_syntax.py")).is_valid


def _program_path(path):
    return os.path.join(os.path.dirname(__file__), "programs", path)
