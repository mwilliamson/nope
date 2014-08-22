import collections


class _Attribute(object):
    def __init__(self, name, type_, read_only=False):
        self.name = name
        self.type = type_
        self.read_only = read_only
    
    def substitute_types(self, type_map):
        return _Attribute(self.name, _substitute_types(self.type, type_map), self.read_only)


attr = _Attribute


class _Attributes(object):
    def __init__(self, attrs):
        self._attrs = attrs
    
    def add(self, name, type_, read_only=False):
        self._attrs[name] = _Attribute(name, type_, read_only=read_only)
    
    def get(self, name):
        return self._attrs.get(name)
    
    def type_of(self, name):
        if name in self._attrs:
            return self._attrs[name].type
        else:
            return None
    
    def __contains__(self, name):
        return name in self._attrs
    
    def substitute_types(self, type_map):
        return _Attributes(dict(
            (name, _substitute_types(attr_type, type_map))
            for name, attr_type in self._attrs.items()
        ))
    
    def __iter__(self):
        return iter(self._attrs.values())


class _GenericTypeAttributes(object):
    def __init__(self, params, attrs):
        self._params = params
        self._attrs = attrs
    
    def add(self, name, type_, read_only=False):
        self._attrs.add(name, type_(*self._params), read_only=read_only)


class _ScalarType(object):
    def __init__(self, name, attrs, base_classes):
        assert isinstance(attrs, _Attributes)
        
        self.name = name
        self.attrs = attrs
        self.base_classes = base_classes
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return str(self)
    
    def substitute_types(self, type_map):
        return self


def scalar_type(name, attrs=None, base_classes=None):
    if base_classes is None:
        base_classes = []
    
    return _ScalarType(name, _generate_attrs(attrs), base_classes)


def _generate_attrs(attrs):
    return _Attributes(dict((attr.name, attr) for attr in (attrs or [])))


# TODO: number of type params
class _GenericType(object):
    def __init__(self, params, underlying_type):
        self.underlying_type = underlying_type
        self.params = params
        self.attrs = _GenericTypeAttributes(params, underlying_type.attrs)
    
    def __call__(self, *args):
        return self.instantiate(list(args))
    
    def instantiate(self, params):
        param_map = dict(zip(self.params, params))
        instantiated_attrs = _substitute_types(self.underlying_type.attrs, param_map)
        return InstantiatedType(self, params, instantiated_attrs)
    
    def is_instantiated_type(self, other):
        # TODO: handle subtyping
        return isinstance(other, InstantiatedType) and other.generic_type == self
    
    def __str__(self):
        return self.name
        
    def __repr__(self):
        return str(self)


def _generic_type(params, underlying_type, attrs=None):
    if attrs is None:
        attrs = {}
    
    formal_params = [_FormalParameter(param) for param in params]
    param_map = dict(zip(params, formal_params))
    generic_class = _GenericType(formal_params, underlying_type)
    
    for attr in attrs:
        generic_class.attrs.add(attr.name, attr.type, attr.read_only)
    
    return generic_class


def generic_class(name, params, attrs=None):
    return _generic_type(params, scalar_type(name), attrs)


def _substitute_types(type_, type_map):
    return type_.substitute_types(type_map)


class _FormalParameter(object):
    def __init__(self, name):
        self._name = name
    
    def substitute_types(self, type_map):
        return type_map.get(self, self)


class InstantiatedType(object):
    def __init__(self, generic_type, params, attrs):
        assert isinstance(attrs, _Attributes)
        
        self.generic_type = generic_type
        self.params = params
        self.attrs = attrs
    
    def substitute_types(self, type_map):
        # TODO: test shadowing
        
        instantiated_params = [
            _substitute_types(param_type, type_map)
            for param_type in self.params
        ]
        instantiated_attrs = _substitute_types(self.attrs, type_map)
        return InstantiatedType(self.generic_type, instantiated_params, instantiated_attrs)
    
    def __eq__(self, other):
        if not isinstance(other, InstantiatedType):
            return False
            
        return self.generic_type == other.generic_type and self.params == other.params
    
    def __neq__(self, other):
        return not (self == other)
    
    def __str__(self):
        return "{}[{}]".format(self.generic_type, ", ".join(map(str, self.params)))
    
    def __repr__(self):
        return str(self)


class _StructuralType(object):
    def __init__(self, name, attrs):
        assert isinstance(attrs, _Attributes)
        
        self.name = name
        self.attrs = attrs


def structural_type(name, attrs=None):
    return _StructuralType(name, _generate_attrs(attrs))

def generic_structural_type(name, params, attrs=None):
    return _generic_type(params, structural_type(name, {}), attrs)

    
MetaType = collections.namedtuple("MetaType", ["type", "attrs"])
    

class _FunctionType(object):
    def __init__(self, args, return_type):
        self.args = args
        self.return_type = return_type
    
    def substitute_types(self, type_map):
        return _FunctionType(
            [_substitute_types(arg, type_map) for arg in self.args],
            _substitute_types(self.return_type, type_map)
        )
    
    def __eq__(self, other):
        if not isinstance(other, _FunctionType):
            return False
        
        return (self.args, self.return_type) == (other.args, other.return_type)
    
    def __neq__(self, other):
        return not (self == other)


class _FunctionTypeArgument(object):
    def __init__(self, name, type_):
        self.name = name
        self.type = type_
    
    def substitute_types(self, type_map):
        return _FunctionTypeArgument(
            self.name,
            _substitute_types(self.type, type_map),
        )
    
    def __eq__(self, other):
        if not isinstance(other, _FunctionTypeArgument):
            return False
        
        return (self.name, self.type) == (other.name, other.type)
    
    def __neq__(self, other):
        return not (self == other)


def func(args, return_type):
    def convert_arg(arg):
        if isinstance(arg, _FunctionTypeArgument):
            return arg
        else:
            return _FunctionTypeArgument(None, arg)
    
    return _FunctionType(list(map(convert_arg, args)), return_type)


def func_arg(name, type):
    return _FunctionTypeArgument(name, type)


def is_func_type(type_):
    return isinstance(type_, _FunctionType)


class _UnionType(object):
    def __init__(self, types):
        self._types = types


def union(*types):
    return _UnionType(types)


def is_sub_type(super_type, sub_type):
    if super_type == object_type:
        return True
    
    if isinstance(sub_type, _ScalarType) and super_type in sub_type.base_classes:
        return True
    
    if isinstance(super_type, _StructuralType):
        return all(
            is_sub_type(attr.type, sub_type.attrs.type_of(attr.name))
            for attr in super_type.attrs
        )
    
    return super_type == sub_type


def meta_type(name, attrs=None):
    return MetaType(name, _generate_attrs(attrs))


def is_meta_type(type_):
    return isinstance(type_, MetaType)


any_type = object_type = scalar_type("object")

none_type = scalar_type("NoneType")

boolean_type = scalar_type("BooleanType")

int_type = scalar_type("int")

float_type = scalar_type("float")

int_type.attrs.add("__add__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__sub__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__mul__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__truediv__", func([int_type], float_type), read_only=True)
int_type.attrs.add("__floordiv__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__mod__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__pow__", func([int_type], union(int_type, float_type)), read_only=True)
int_type.attrs.add("__lshift__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__rshift__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__and__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__or__", func([int_type], int_type), read_only=True)
int_type.attrs.add("__xor__", func([int_type], int_type), read_only=True)

int_type.attrs.add("__neg__", func([], int_type), read_only=True)
int_type.attrs.add("__pos__", func([], int_type), read_only=True)
int_type.attrs.add("__abs__", func([], int_type), read_only=True)
int_type.attrs.add("__invert__", func([], int_type), read_only=True)

str_type = scalar_type("str")
str_type.attrs.add("find", func([str_type], int_type), read_only=True)

str_meta_type = meta_type(str_type, [
    attr("__call__", func([any_type], str_type), read_only=True),
])

# TODO: should be a structural type (with __next__)
iterator = generic_structural_type("iterator", ["T"])
iterator.attrs.add("__iter__", lambda T: func([], iterator(T)), read_only=True)
iterator.attrs.add("__next__", lambda T: func([], T), read_only=True)

iterable = generic_structural_type("iterable", ["T"])
iterable.attrs.add("__iter__", lambda T: func([], iterator(T)), read_only=True)

list_type = generic_class("list", ["T"], [
    attr("__getitem__", lambda T: func([int_type], T), read_only=True),
    attr("__setitem__", lambda T: func([int_type, T], none_type), read_only=True),
    attr("__iter__", lambda T: func([], iterator(T)), read_only=True),
    attr("append", lambda T: func([T], none_type), read_only=True),
])

bottom_type = scalar_type("bottom")

exception_type = scalar_type("Exception")
exception_meta_type = meta_type(exception_type, [
    attr("__call__", func([str_type], exception_type)),
])

traceback_type = scalar_type("traceback")

assertion_error_type = scalar_type("AssertionError", base_classes=[exception_type])
assertion_error_meta_type = meta_type(assertion_error_type, [
    attr("__call__", func([str_type], assertion_error_type)),
])


tuple2 = generic_class("tuple2", ["A", "B"])

def tuple(*args):
    assert len(args) == 2
    return tuple2(*args)


def unify(types):
    if len(types) == 0:
        return bottom_type
        
    for type_ in types:
        if not is_sub_type(types[0], type_):
            return object_type
    
    return types[0]


class _Module(object):
    def __init__(self, name, attrs):
        self.name = name
        self.attrs = attrs


def module(name, attrs):
    return _Module(name, _generate_attrs(attrs))


class TypeLookup(object):
    def __init__(self, types):
        self._types = types
    
    def type_of(self, node):
        return self._types.get(id(node))
