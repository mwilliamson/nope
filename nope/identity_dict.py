class IdentityDict(object):
    def __init__(self, values=None):
        if values is None:
            values = []
        
        self._values = {}
        
        for key, value in values:
            self._values[id(key)] = value
        
    
    def __setitem__(self, key, value):
        self._values[id(key)] = value
    
    def __getitem__(self, key):
        try:
            return self._values[id(key)]
        except KeyError:
            raise KeyError("id({}) == {}".format(repr(key), id(key)))
    
    def __contains__(self, key):
        return id(key) in self._values
    
    def get(self, key, default=None):
        return self._values.get(id(key), default)
