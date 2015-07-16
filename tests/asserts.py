def assert_raises(exception_type, func):
    try:
        func()
        assert False, "Expected exception: {0}".format(exception_type)
    except exception_type as exception:
        return exception
