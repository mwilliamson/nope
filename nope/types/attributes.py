
class Attribute(object):
    def __init__(self, name, type_, read_only=True):
        self.name = name
        self.type = type_
        self.read_only = read_only
    
    def __repr__(self):
        return "_Attribute({}, {}, {})".format(self.name, self.type, self.read_only)


def attrs_from_iterable(attrs):
    return _Attributes(dict((attr.name, attr) for attr in (attrs or [])))


class _Attributes(object):
    def __init__(self, attrs):
        self._attrs = attrs
    
    def add(self, name, type_, read_only=True):
        self._attrs[name] = Attribute(name, type_, read_only=read_only)
    
    def get(self, name):
        return self._attrs.get(name)
    
    def type_of(self, name):
        if name in self._attrs:
            return self._attrs[name].type
        else:
            return None
    
    def __contains__(self, name):
        return name in self._attrs
    
    def __iter__(self):
        return iter(self._attrs.values())
    
    def copy(self):
        return _Attributes(self._attrs.copy())
    
    def names(self):
        return self._attrs.keys()
    
    def __repr__(self):
        return "Attributes({})".format(self._attrs)


class EmptyAttributes(object):
    def get(self, name):
        return None
    
    def type_of(self, name):
        return None
    
    def __contains__(self, name):
        return False
    
    def __iter__(self):
        return iter([])
    
    def copy(self):
        return self
    
    def names(self):
        return []
