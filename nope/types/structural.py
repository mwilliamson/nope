from .attributes import attrs_from_iterable


class _StructuralType(object):
    def __init__(self, name, attrs):
        self.name = name
        self.attrs = attrs
    
    def __str__(self):
        return self.name


def is_structural_type(type_):
    return isinstance(type_, _StructuralType)
    

def structural_type(name, attrs=None):
    return _StructuralType(name, attrs_from_iterable(attrs))
