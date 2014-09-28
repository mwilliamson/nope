import collections

from .identity_dict import IdentityDict


class _Attribute(object):
    def __init__(self, name, type_, read_only=False):
        self.name = name
        self.type = type_
        self.read_only = read_only
    
    def substitute_types(self, type_map):
        return _Attribute(self.name, _substitute_types(self.type, type_map), self.read_only)
    
    def __repr__(self):
        return "_Attribute({}, {}, {})".format(self.name, self.type, self.read_only)


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
        if hasattr(underlying_type, "attrs"):
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
        return self.underlying_type.name
        
    def __repr__(self):
        return str(self)


def is_generic_type(type_):
    return isinstance(type_, _GenericType)


def _generic_type(params, underlying_type, attrs=None):
    if attrs is None:
        attrs = {}
    
    formal_params = [_formal_param(param) for param in params]
    param_map = dict(zip(params, formal_params))
    generic_class = _GenericType(formal_params, underlying_type)
    
    for attr in attrs:
        generic_class.attrs.add(attr.name, attr.type, attr.read_only)
    
    return generic_class


def generic(params, create_underlying_type):
    formal_params = [_formal_param(param) for param in params]
    param_map = dict(zip(params, formal_params))
    return _GenericType(formal_params, create_underlying_type(*formal_params))


def generic_class(name, params, attrs=None):
    return _generic_type(params, scalar_type(name), attrs)


def _substitute_types(type_, type_map):
    return type_.substitute_types(type_map)


class _Variance(object):
    Invariant, Covariant, Contravariant = range(3)


class _FormalParameter(object):
    def __init__(self, name, variance):
        self._name = name
        self.variance = variance
    
    def substitute_types(self, type_map):
        return type_map.get(self, self)
    
    def __repr__(self):
        return "_FormalParameter({}, {})".format(self._name, self.variance)


def _formal_param(param):
    if isinstance(param, _FormalParameter):
        return param
    else:
        return _FormalParameter(param, _Variance.Invariant)


def invariant(name):
    return _FormalParameter(name, _Variance.Invariant)


def covariant(name):
    return _FormalParameter(name, _Variance.Covariant)


def contravariant(name):
    return _FormalParameter(name, _Variance.Contravariant)


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
    
    def __str__(self):
        args_str = ", ".join(map(str, self.args))
        return "{} -> {}".format(args_str, self.return_type)
    
    def __repr__(self):
        return str(self)


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
    
    def __str__(self):
        if self.name is None:
            return str(self.type)
        else:
            return "{}: {}".format(self.name, self.type)


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
    # Note that callable types may not be func types
    # For instance, classe with a __call__ method are callable, but not func types
    return isinstance(type_, _FunctionType)


def is_generic_func_type(type_):
    return isinstance(type_, _GenericType) and isinstance(type_.underlying_type, _FunctionType)


class _UnionTypeBase(object):
    def __init__(self, types):
        self._types = list(types)
    
    def substitute_types(self, type_map):
        return type(self)([_substitute_types(type_, type_map) for type_ in self._types])
    
    def __str__(self):
        return " | ".join(map(str, self._types))
    
    def __repr__(self):
        return "{}({})".format(self._union_type_name, ", ".join(map(repr, self._types)))
    
    def __eq__(self, other):
        if not isinstance(other, _UnionTypeBase):
            return False
        return (self._union_type_name, self._types) == (other._union_type_name, other._types)
    
    def __neq__(self, other):
        return not (self == other)


class _UnionType(_UnionTypeBase):
    _union_type_name = "union"


class _OverloadedFunctionType(_UnionTypeBase):
    _union_type_name = "overloaded_func"


def union(*types):
    return _UnionType(types)


def is_union_type(type_):
    return isinstance(type_, _UnionType)


def overloaded_func(*func_types):
    for func_type in func_types:
        assert is_func_type(func_type)
    return _OverloadedFunctionType(func_types)


def is_overloaded_func_type(type_):
    return isinstance(type_, _OverloadedFunctionType)


def is_sub_type(super_type, sub_type, unify=None):
    if unify is None:
        unify = set()
    else:
        unify = set(unify)
    
    constraints = Constraints()

    def is_matching_type(formal_type_param, super_type_param, sub_type_param):
        if formal_type_param.variance == _Variance.Covariant:
            return is_sub_type(super_type_param, sub_type_param)
        elif formal_type_param.variance == _Variance.Contravariant:
            return is_sub_type(sub_type_param, super_type_param)
        else:
            # TODO: fix type equality and use it here (either by implementing
            # type equality using sub-typing or implementing type substitution)
            return is_sub_type(super_type_param, sub_type_param) and is_sub_type(sub_type_param, super_type_param)
    
    def is_sub_type(super_type, sub_type):
        if super_type == object_type:
            return True
        
        if isinstance(sub_type, _UnionType):
            return all(
                is_sub_type(super_type, possible_sub_type)
                for possible_sub_type in sub_type._types
            )
        
        if (isinstance(sub_type, _ScalarType) and
                any(is_sub_type(super_type, base_class)
                for base_class in sub_type.base_classes)):
            return True
        
        if isinstance(super_type, _StructuralType):
            return all(
                is_sub_type(attr.type, sub_type.attrs.type_of(attr.name))
                for attr in super_type.attrs
            )
        
        if isinstance(super_type, _UnionType):
            return any(
                is_sub_type(possible_super_type, sub_type)
                for possible_super_type in super_type._types
            )
        
        if (isinstance(super_type, InstantiatedType) and
                isinstance(sub_type, InstantiatedType) and
                super_type.generic_type == sub_type.generic_type):
            return all(map(is_matching_type, super_type.generic_type.params, super_type.params, sub_type.params))
        
        if isinstance(super_type, _FormalParameter) and super_type in unify:
            constraints.constrain_type_param_to_super_type(super_type, sub_type)
            return True
        
        if isinstance(sub_type, _FormalParameter) and sub_type in unify:
            constraints.constrain_type_param_to_sub_type(sub_type, super_type)
            return True
        
        if isinstance(super_type, _FunctionType) and (sub_type, _FunctionType):
            if len(super_type.args) != len(sub_type.args):
                return False
            
            for super_arg, sub_arg in zip(super_type.args, sub_type.args):
                if super_arg.name is not None and sub_arg.name != super_arg.name:
                    return False
                if not is_sub_type(sub_arg.type, super_arg.type):
                    return False
            
            return is_sub_type(super_type.return_type, sub_type.return_type)
        
        return super_type == sub_type

    
    if is_sub_type(super_type, sub_type):
        return constraints.resolve()
    else:
        return None


class Constraints(object):
    def __init__(self):
        self._constraints = {}
    
    def resolve(self):
        type_map = dict(
            (type_param, self._resolve_constraints(constraints))
            for type_param, constraints in self._constraints.items()
        )
        
        if any(value is None for value in type_map.values()):
            return None
        else:
            return TypeMap(type_map)
    
    def _resolve_constraints(self, constraints):
        types = set(type_ for relation, type_ in constraints)
        
        if len(types) == 1:
            return next(iter(types))
        
        relations = set(relation for relation, type_ in constraints)
        if relations == set(["super"]):
            return common_super_type(types)
        elif relations == set(["sub"]):
            return common_sub_type(types)
        else:
            return None
        
    
    def constrain_type_param_to_super_type(self, type_param, sub_type):
        self._add_constraint(type_param, ("super", sub_type))
    
    def constrain_type_param_to_sub_type(self, type_param, super_type):
        self._add_constraint(type_param, ("sub", super_type))
    
    def _add_constraint(self, type_param, constraint):
        if type_param not in self._constraints:
            self._constraints[type_param] = []
        
        self._constraints[type_param].append(constraint)


class TypeMap(object):
    def __init__(self, type_map):
        self._type_map = type_map
    
    def __getitem__(self, key):
        return self._type_map[key]
    
    def get(self, key, default):
        return self._type_map.get(key, default)


def meta_type(type_, attrs=None):
    return MetaType(type_, _generate_attrs(attrs))


def is_meta_type(type_):
    return isinstance(type_, MetaType)


any_type = object_type = scalar_type("object")

bottom_type = scalar_type("bottom")

def common_super_type(types):
    if len(types) == 0:
        return bottom_type
    
    first_type = next(iter(types))
    
    for type_ in types:
        if not is_sub_type(first_type, type_):
            return object_type
    
    return first_type


def common_sub_type(types):
    if len(types) == 0:
        return any_type
    
    first_type = next(iter(types))
    
    for type_ in types:
        if not is_sub_type(type_, first_type):
            return bottom_type
    
    return first_type


class _Module(object):
    def __init__(self, name, attrs):
        self.name = name
        self.attrs = attrs


def module(name, attrs):
    return _Module(name, _generate_attrs(attrs))


class TypeLookup(object):
    def __init__(self, types):
        assert isinstance(types, IdentityDict)
        
        self._types = types
    
    def type_of(self, node):
        return self._types.get(node)

from .builtin_types import (
    none_type,
    int_type,
    boolean_type, bool_meta_type,
    str_type, str_meta_type,
    list_type, list_meta_type,
    dict_type, dict_meta_type,
    tuple,
    slice_type,
    iterable,
    iterator,
    has_len,
    exception_type, exception_meta_type,
    assertion_error_type, assertion_error_meta_type,
    traceback_type,
)
