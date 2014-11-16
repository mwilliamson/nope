import itertools

from nose.tools import istest, assert_equal, assert_raises

from nope import caching


@istest
def function_returns_cached_result_when_args_are_equal():
    counter = itertools.count(0)
    
    @caching.cached()
    def val(*args):
        return next(counter), args
    
    assert_equal((0, ()), val())
    assert_equal((0, ()), val())
    
    assert_equal((1, (2, 4)), val(2, 4))
    assert_equal((2, (2, 5)), val(2, 5))
    assert_equal((1, (2, 4)), val(2, 4))


@istest
def cached_function_has_same_name_as_original_function():
    @caching.cached()
    def val(*args):
        return
        
    assert_equal("val", val.__name__)


@istest
def error_is_raised_if_cycle_is_detected():
    @caching.cached()
    def val(x):
        if x < 10:
            return x
        else:
            return val(x)
        
    assert_equal(4, val(4))
    assert_raises(caching.CycleError, lambda: val(14))


@istest
def can_set_value_to_return_if_cycle_is_detected():
    @caching.cached(cycle_value=42)
    def val():
        return val()
        
    assert_equal(42, val())
