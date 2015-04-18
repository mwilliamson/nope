from .attributes import attrs_from_iterable


class _StructuralType(object):
    def __init__(self, name, attrs):
        self.name = name
        self.attrs = attrs
    
    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if not isinstance(other, _StructuralType):
            return False
        
        return (self.name, self.attrs) == (other.name, other.attrs)
    
    def __ne__(self, other):
        return not (self == other)
    
    def __hash__(self):
        return hash((self.name, self.attrs))
    
    def __repr__(self):
        return "StructuralType({}, {})".format(self.name, self.attrs)


def is_structural_type(type_):
    return isinstance(type_, _StructuralType)
    

def structural_type(name, attrs=None):
    return _StructuralType(name, attrs_from_iterable(attrs))
