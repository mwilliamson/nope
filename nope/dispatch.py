class TypeDispatch(object):
    def __init__(self, funcs, *, default):
        self._funcs = funcs
        self._default = default
    
    def __call__(self, first, *args, **kwargs):
        func = self._funcs.get(type(first), self._default)
        return func(first, *args, **kwargs)
