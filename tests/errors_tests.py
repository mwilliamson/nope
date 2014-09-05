from nose.tools import istest, assert_equal

from nope import errors, types


@istest
def unexpected_value_type_error_str_contains_expected_and_actual_types():
	error = errors.UnexpectedValueTypeError(None,
		expected=types.int_type,
		actual=types.str_type,
	)
	assert_equal("Expected value of type 'int' but was of type 'str'", str(error))
