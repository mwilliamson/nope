def filter_by_type(type_filter, iterable):
    return [value for value in iterable if isinstance(value, type_filter)]
