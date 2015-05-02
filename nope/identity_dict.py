import collections


class _IdentityDict(object):
    def __init__(self, key_identity, values):
        self._key_identity = key_identity
        self._values = collections.OrderedDict()
        
        for key, value in values:
            self[key] = value
        
    
    def __setitem__(self, key, value):
        self._values[self._key_identity(key)] = (key, value)
    
    def __getitem__(self, key):
        try:
            return self._values[self._key_identity(key)][1]
        except KeyError:
            raise KeyError("key_identity({}) == {}".format(repr(key), self._key_identity(key)))
    
    def __contains__(self, key):
        return self._key_identity(key) in self._values
    
    def get(self, key, default=None):
        return self._values.get(self._key_identity(key), (None, default))[1]
    
    def keys(self):
        return [key for key, value in self._values.values()]
    
    def pop(self, key):
        return self._values.pop(self._key_identity(key))[1]
    
    def popitem(self):
        return self._values.popitem()[1]
    
    def __bool__(self):
        return bool(self._values)


class NodeDict(_IdentityDict):
    @staticmethod
    def create(values):
        if not isinstance(values, NodeDict):
            return NodeDict(values)
        else:
            return values
            
    def __init__(self, values=None):
        if values is None:
            values = []
        super().__init__(key_identity=lambda node: node.node_id, values=values)


class ComputedNodeDict(object):
    def __init__(self, generate_value):
        self._values = NodeDict()
        self._generate_value = generate_value
    
    def __getitem__(self, key):
        if key not in self._values:
            self._values[key] = self._generate_value(key)
        
        return self._values[key]
