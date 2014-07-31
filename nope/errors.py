class TypeCheckError(Exception):
    pass


class ArgumentsLengthError(TypeCheckError):
    def __init__(self, node, expected, actual):
        self.node = node
        self.expected = expected
        self.actual = actual


class TypeMismatchError(TypeCheckError):
    def __init__(self, node, expected, actual):
        self.expected = expected
        self.actual = actual
        self.node = node
        
    def __str__(self):
        return "Expected {0} but was {1}".format(self.expected, self.actual)


class UnboundLocalError(TypeCheckError):
    def __init__(self, node, name):
        self.node = node
        self.name = name
    
    def __str__(self):
        return "local variable {0} referenced before assignment".format(self.name)


class AttributeError(TypeCheckError):
    def __init__(self, node, obj_type, attr_name):
        self.node = node
        self._obj_type = obj_type
        self._attr_name = attr_name
    
    def __str__(self):
        return "{} object has no attribute {}".format(self._obj_type, self._attr_name)


class ImportError(TypeCheckError):
    def __init__(self, node, message):
        self.node = node
        self._message = message
    
    def __str__(self):
        return self._message


class ImportedValueRedeclaration(TypeCheckError):
    def __init__(self, node):
        # TODO: __str__
        self.node = node
