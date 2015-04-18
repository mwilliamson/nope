import collections

import zuice

from ..identity_dict import NodeDict
from .. import caching
from ..iterables import find
from .attributes import attrs_from_iterable, Attribute, EmptyAttributes
from .classes import class_type, is_class_type
from .structural import structural_type, is_structural_type
from .generics import (
    generic, unnamed_generic, generic_class, generic_structural_type, generic_func,
    invariant, covariant, contravariant, Variance as _Variance,
    is_formal_parameter, is_generic_type, is_instantiated_type, is_generic_func,
)


attr = Attribute

    
MetaType = collections.namedtuple("MetaType", ["type", "attrs"])
    

class _FunctionType(object):
    def __init__(self, args, return_type):
        self.args = tuple(args)
        self.return_type = return_type
        self.attrs = EmptyAttributes()
    
    def __eq__(self, other):
        if not isinstance(other, _FunctionType):
            return False
        
        return (self.args, self.return_type) == (other.args, other.return_type)
    
    def __neq__(self, other):
        return not (self == other)
    
    def __hash__(self):
        return hash((self.args, self.return_type))
    
    def __str__(self):
        args_str = ", ".join(map(str, self.args))
        return "{} -> {}".format(args_str, self.return_type)
    
    def __repr__(self):
        return str(self)


class _FunctionTypeArgument(object):
    def __init__(self, name, type_, optional):
        self.name = name
        self.type = type_
        self.optional = optional
    
    def __eq__(self, other):
        if not isinstance(other, _FunctionTypeArgument):
            return False
        
        return (self.name, self.type, self.optional) == (other.name, other.type, other.optional)
    
    def __neq__(self, other):
        return not (self == other)
    
    def __hash__(self):
        return hash((self.name, self.type, self.optional))
    
    def __str__(self):
        if self.name is None:
            with_name = str(self.type)
        else:
            with_name = "{}: {}".format(self.name, self.type)
        
        if self.optional:
            return "?" + with_name
        else:
            return with_name


def func(args, return_type):
    def convert_arg(arg):
        if isinstance(arg, _FunctionTypeArgument):
            return arg
        else:
            return _FunctionTypeArgument(None, arg, optional=False)
    
    return _FunctionType(list(map(convert_arg, args)), return_type)


def func_arg(name, type, optional=False):
    return _FunctionTypeArgument(name, type, optional=optional)


def is_func_type(type_):
    # Note that callable types may not be func types
    # For instance, classe with a __call__ method are callable, but not func types
    return isinstance(type_, _FunctionType)


def is_generic_func_type(type_):
    return isinstance(type_, _GenericType) and isinstance(type_.underlying_type, _FunctionType)


class _UnionTypeBase(object):
    def __init__(self, types):
        self._types = tuple(types)
        self.attrs = EmptyAttributes()
    
    def __str__(self):
        return " | ".join(map(str, self._types))
    
    def __repr__(self):
        return "{}({})".format(self._union_type_name, ", ".join(map(repr, self._types)))
    
    def __eq__(self, other):
        if not isinstance(other, _UnionTypeBase):
            return False
        return (self._union_type_name, frozenset(self._types)) == (other._union_type_name, frozenset(other._types))
    
    def __hash__(self):
        return hash((self._union_type_name, frozenset(self._types)))
    
    def __neq__(self, other):
        return not (self == other)


class _UnionType(_UnionTypeBase):
    _union_type_name = "union"


class _OverloadedFunctionType(_UnionTypeBase):
    _union_type_name = "overloaded_func"


def union(*types):
    unique_types = collections.OrderedDict()
    
    for type_ in types:
        if type_ not in unique_types:
            unique_types[type_] = True
    
    if len(unique_types) == 1:
        return next(iter(unique_types))
    else:
        return _UnionType(list(unique_types.keys()))


def is_union_type(type_):
    return isinstance(type_, _UnionType)


def remove(original, to_remove):
    if is_union_type(original):
        types = tuple(type_ for type_ in original._types if type_ != to_remove)
        return union(*types)
    else:
        return original


def overloaded_func(*func_types):
    for func_type in func_types:
        assert is_func_type(func_type)
    return _OverloadedFunctionType(func_types)


def is_overloaded_func_type(type_):
    return isinstance(type_, _OverloadedFunctionType)


class _UnknownType(object):
    pass

unknown_type = _UnknownType()

def is_unknown(type_):
    return type_ is unknown_type


def is_equivalent_type(first_type, second_type):
    return is_sub_type(first_type, second_type) and is_sub_type(second_type, first_type)


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
    
    @caching.cached(cycle_value=False)
    def is_sub_type(super_type, sub_type):
        assert super_type is not None
        assert sub_type is not None
        
            
        if is_formal_parameter(super_type) and super_type in unify:
            constraints.constrain_type_param_to_super_type(super_type, sub_type)
            return True
        
        if is_formal_parameter(sub_type) and sub_type in unify:
            constraints.constrain_type_param_to_sub_type(sub_type, super_type)
            return True
            
        if super_type == sub_type:
            return True
        
        if super_type == object_type:
            return True
        
        if sub_type == bottom_type:
            return True
            
        if super_type == any_meta_type and is_meta_type(sub_type):
            return True
        
        if _instance_of_same_generic_type(super_type, sub_type):
            return all(map(is_matching_type, super_type.generic_type.params, super_type.type_params, sub_type.type_params))
        
        if is_instantiated_type(super_type):
            return is_sub_type(super_type.reify(), sub_type)
            
        if is_instantiated_type(sub_type):
            return is_sub_type(super_type, sub_type.reify())
        
        if isinstance(sub_type, _UnionType):
            return all(
                is_sub_type(super_type, possible_sub_type)
                for possible_sub_type in sub_type._types
            )
        
        if isinstance(super_type, _UnionType):
            return any(
                is_sub_type(possible_super_type, sub_type)
                for possible_super_type in super_type._types
            )
        
        if (is_class_type(sub_type) and
                any(is_sub_type(super_type, base_class)
                for base_class in sub_type.base_classes)):
            return True
        
        if is_structural_type(super_type):
            return all(
                attr.name in sub_type.attrs and is_sub_type(attr.type, sub_type.attrs.type_of(attr.name))
                for attr in super_type.attrs
            )
        
        if isinstance(super_type, _FunctionType) and (sub_type, _FunctionType):
            if len(super_type.args) != len(sub_type.args):
                return False
            
            for super_arg, sub_arg in zip(super_type.args, sub_type.args):
                if super_arg.name is not None and sub_arg.name != super_arg.name:
                    return False
                if not is_sub_type(sub_arg.type, super_arg.type):
                    return False
            
            return is_sub_type(super_type.return_type, sub_type.return_type)
        
        return False

    
    if is_sub_type(super_type, sub_type):
        return constraints.resolve()
    else:
        return None


def _instance_of_same_generic_type(first, second):
    if not is_instantiated_type(first):
        return False
        
    if not is_instantiated_type(second):
        return False
    
    return first.generic_type == second.generic_type


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
        
        required_sub_types = set(
            type_
            for relation, type_ in constraints
            if relation == "super"
        )
        super_type = common_super_type(required_sub_types)
        
        required_super_types = set(
            type_
            for relation, type_ in constraints
            if relation == "sub"
        )
        sub_type = common_sub_type(required_super_types)
        
        if len(required_sub_types) == 0:
            return sub_type
        elif is_sub_type(sub_type, super_type):
            return super_type
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


def is_instantiated_sub_type(generic_type, other):
    return is_sub_type(generic_type.instantiate(generic_type.params), other, unify=generic_type.params)


class TypeMap(object):
    def __init__(self, type_map):
        self._type_map = type_map
    
    def __getitem__(self, key):
        return self._type_map[key]
    
    def get(self, key, default):
        return self._type_map.get(key, default)


def meta_type(type_, attrs=None):
    return MetaType(type_, attrs_from_iterable(attrs))


def is_meta_type(type_):
    return isinstance(type_, MetaType)


any_type = object_type = class_type("object")
any_meta_type = class_type("type")

bottom_type = class_type("bottom")

def common_super_type(types):
    if len(types) == 0:
        return bottom_type
    
    super_type = find(
        lambda possible_super_type: all(
            is_sub_type(possible_super_type, type_)
            for type_ in types
        ),
        types,
    )
    
    if super_type is None:
        return union(*types)
    else:
        return super_type


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
    
    def copy(self):
        return _Module(self.name, self.attrs.copy())
    
    def __str__(self):
        return "module '{}'".format(self.name)


def module(name, attrs):
    return _Module(name, attrs_from_iterable(attrs))


class TypeLookup(object):
    def __init__(self, types):
        assert isinstance(types, NodeDict)
        
        self._types = types
    
    def type_of(self, node):
        return self._types.get(node)


TypeLookupFactory = zuice.key("TypeLookupFactory")


from ..builtin_types import (
    none_type,
    int_type,
    bool_type, bool_meta_type,
    str_type, str_meta_type,
    list_type, list_meta_type,
    dict_type, dict_meta_type,
    tuple_type,
    slice_type, is_tuple,
    iterable,
    iterator,
    has_len,
    exception_type, exception_meta_type,
    assertion_error_type, assertion_error_meta_type,
    traceback_type,
)
