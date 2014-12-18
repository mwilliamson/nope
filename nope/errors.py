class TypeCheckError(Exception):
    pass


class UnsupportedError(TypeCheckError):
    def __init__(self, message):
        self._message = message
        
    def __str__(self):
        return self._message


class UndefinedNameError(TypeCheckError):
    def __init__(self, node, name):
        self.node = node
        self.name = name
    
    def __str__(self):
        return "name '{0}' is not defined".format(self.name)


class InvalidReassignmentError(TypeCheckError):
    def __init__(self, node, message):
        self.node = node
        self._message = message
    
    def __str__(self):
        return self._message


class ArgumentsError(TypeCheckError):
    def __init__(self, node, message):
        self.node = node
        self.message = message
    
    def __str__(self):
        return self.message


class MethodHasNoArgumentsError(TypeCheckError):
    def __init__(self, class_node, attr_name):
        self.node = class_node
        self.attr_name = attr_name
    
    def __str__(self):
        return "'{}' method must have at least one argument".format(self.attr_name)


class UnexpectedReceiverTypeError(TypeCheckError):
    def __init__(self, class_node, receiver_type):
        self.node = class_node
        self.receiver_type = receiver_type
    
    def __str__(self):
        return "first argument of methods should have Self type but was {}".format(
            _quote_type(self.receiver_type))


class UnexpectedValueTypeError(TypeCheckError):
    def __init__(self, node, expected, actual):
        self.expected = expected
        self.actual = actual
        self.node = node
        
    def __str__(self):
        return "Expected value of type {} but was of type {}".format(
            _quote_type(self.expected), _quote_type(self.actual))


class UnexpectedTargetTypeError(TypeCheckError):
    def __init__(self, node, target_type, value_type):
        self.node = node
        self.target_type = target_type
        self.value_type = value_type
    
    def __str__(self):
        return "Target has type {} but value has type {}".format(
            _quote_type(self.target_type), _quote_type(self.value_type))


class UnpackError(TypeCheckError):
    def __init__(self, node, target_length, value_length):
        self.node = node
        self._target_length = target_length
        self._value_length = value_length
    
    def __str__(self):
        return "need {} values to unpack, but only have {}".format(self._target_length, self._value_length)


class CanOnlyUnpackTuplesError(TypeCheckError):
    def __init__(self, node):
        self.node = node
    
    def __str__(self):
        return "only tuples can be unpacked"


class InitMethodsMustReturnNoneError(TypeCheckError):
    def __init__(self, node):
        self.node = node
    
    def __str__(self):
        return "__init__ methods must return None"


class InitMethodCannotGetSelfAttributes(TypeCheckError):
    def __init__(self, node):
        self.node = node
    
    def __str__(self):
        return "__init__ methods cannot get attributes of self"


class InitAttributeMustBeFunctionDefinitionError(TypeCheckError):
    def __init__(self, node):
        self.node = node
    
    def __str__(self):
        return "__init__ attribute must be a function definition"


class UnboundLocalError(TypeCheckError):
    def __init__(self, node, name):
        self.node = node
        self.name = name
    
    def __str__(self):
        return "local variable '{0}' referenced before assignment".format(self.name)


class NoSuchAttributeError(TypeCheckError):
    def __init__(self, node, obj_type, attr_name):
        self.node = node
        self._obj_type = obj_type
        self._attr_name = attr_name
    
    def __str__(self):
        return "'{}' object has no attribute '{}'".format(self._obj_type, self._attr_name)


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
        return "Function must return value of type {}".format(
            _quote_type(self._return_type))


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


def _quote_type(type_):
    if isinstance(type_, str):
        return '"{}"'.format(type_)
    else:
        return "'{}'".format(type_)
