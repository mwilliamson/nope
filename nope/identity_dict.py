import collections


class IdentityDict(object):
    @staticmethod
    def create(values):
        if not isinstance(values, IdentityDict):
            return IdentityDict(values)
        else:
            return values
    
    def __init__(self, values=None):
        if values is None:
            values = []
        
        self._values = collections.OrderedDict()
        
        for key, value in values:
            self[key] = value
        
    
    def __setitem__(self, key, value):
        self._values[id(key)] = (key, value)
    
    def __getitem__(self, key):
        try:
            return self._values[id(key)][1]
        except KeyError:
            raise KeyError("id({}) == {}".format(repr(key), id(key)))
    
    def __contains__(self, key):
        return id(key) in self._values
    
    def get(self, key, default=None):
        return self._values.get(id(key), (None, default))[1]
    
    def keys(self):
        return [key for key, value in self._values.values()]
    
    def pop(self, key):
        return self._values.pop(id(key))[1]
    
    def popitem(self):
        return self._values.popitem()[1]
    
    def __bool__(self):
        return bool(self._values)
