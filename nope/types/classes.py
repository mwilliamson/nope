from .attributes import attrs_from_iterable


class _ScalarType(object):
    def __init__(self, name, attrs, base_classes):
        self.name = name
        self.attrs = attrs
        self.base_classes = base_classes
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return str(self)


def is_class_type(type_):
    return isinstance(type_, _ScalarType)


def scalar_type(name, attrs=None, base_classes=None):
    if base_classes is None:
        base_classes = []
    
    return _ScalarType(name, attrs_from_iterable(attrs), base_classes)
