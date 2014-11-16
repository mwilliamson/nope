import functools


_undefined = object()
_in_progress = object()

def cached(cycle_value=_undefined):
    def create_func(func):
        cache = {}
    
        @functools.wraps(func)
        def cached_func(*args):
            value = cache.get(args, _undefined)
            
            if value is _in_progress:
                if cycle_value is _undefined:
                    raise CycleError()
                else:
                    return cycle_value
            elif value is _undefined:
                cache[args] = _in_progress
                value = cache[args] = func(*args)
                return value
            else:
                return value
        
        return cached_func
    
    return create_func


class CycleError(Exception):
    pass
