from nose.tools import istest, assert_equal

from nope import errors, types


@istest
def unexpected_value_type_error_str_contains_expected_and_actual_types():
    error = errors.UnexpectedValueTypeError(None,
        expected=types.int_type,
        actual=types.str_type,
    )
    assert_equal("Expected value of type 'int' but was of type 'str'", str(error))


@istest
def unexpected_value_type_error_str_uses_string_type_without_quotes():
    error = errors.UnexpectedValueTypeError(None,
        expected="object with '__iter__' method",
        actual=types.int_type,
    )
    assert_equal("Expected value of type \"object with '__iter__' method\" but was of type 'int'", str(error))


@istest
def unexpected_target_type_error_str_contains_target_and_value_types():
    error = errors.UnexpectedTargetTypeError(None,
        target_type=types.int_type,
        value_type=types.str_type,
    )
    assert_equal("Target has type 'int' but value has type 'str'", str(error))


@istest
def missing_return_error_contains_expected_return_type():
    error = errors.MissingReturnError(None, types.int_type)
    assert_equal("Function must return value of type 'int'", str(error))
