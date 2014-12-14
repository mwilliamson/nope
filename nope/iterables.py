def find(predicate, iterable):
    for value in iterable:
        if predicate(value):
            return value
