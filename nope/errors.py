class TypeCheckError(Exception):
    pass


class UndefinedNameError(TypeCheckError):
    def __init__(self, node, name):
        self.node = node
        self.name = name
    
    def __str__(self):
        return "name '{0}' is not defined".format(self.name)


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


class BadAssignmentError(TypeCheckError):
    def __init__(self, node, target_type, value_type):
        self.node = node
        self.target_type = target_type
        self.value_type = value_type
    
    def __str__(self):
        return "Target has type '{}' but value has type '{}'".format(self.target_type, self.value_type)


class UnboundLocalError(TypeCheckError):
    def __init__(self, node, name):
        self.node = node
        self.name = name
    
    def __str__(self):
        return "local variable {0} referenced before assignment".format(self.name)


class NoSuchAttributeError(TypeCheckError):
    def __init__(self, node, obj_type, attr_name):
        self.node = node
        self._obj_type = obj_type
        self._attr_name = attr_name
    
    def __str__(self):
        return "{} object has no attribute {}".format(self._obj_type, self._attr_name)


class ReadOnlyAttributeError(TypeCheckError):
    def __init__(self, node, obj_type, attr_name):
        self.node = node
        self._obj_type = obj_type
        self._attr_name = attr_name
    
    def __str__(self):
        return "'{}' attribute '{}' is read-only".format(self._obj_type, self._attr_name)


class ImportError(TypeCheckError):
    def __init__(self, node, message):
        self.node = node
        self._message = message
    
    def __str__(self):
        return self._message


class ModuleNotFoundError(ImportError):
    pass


class ImportedValueRedeclaration(TypeCheckError):
    def __init__(self, node, name):
        self.node = node
        self._name = name
        
    def __str__(self):
        return "Cannot declare value '{}' in module scope due to child module with the same name".format(self._name)


class AllAssignmentError(TypeCheckError):
    def __init__(self, node, message):
        self.node = node
        self._message = message
    
    def __str__(self):
        return self._message


class MissingReturnError(TypeCheckError):
    def __init__(self, node, return_type):
        self.node = node
        self._return_type = return_type
    
    def __str__(self):
        return "Function must return value of type '{}'".format(self._return_type)


class BadSignatureError(TypeCheckError):
    def __init__(self, node, message):
        self.node = node
        self._message = message
    
    def __str__(self):
        return self._message


class InvalidStatementError(TypeCheckError):
    def __init__(self, node, message):
        self.node = node
        self._message = message
    
    def __str__(self):
        return self._message
