from .types import (
    class_type, meta_type, union, structural_type, generic_structural_type,
    generic_class, func, overloaded_func, generic_func,
    attr,
    any_type, object_type,
    covariant,
)

none_type = class_type("NoneType")

bool_type = class_type("bool")

int_type = class_type("int")

float_type = class_type("float")

int_type.attrs.add("__add__", func([int_type], int_type))
int_type.attrs.add("__sub__", func([int_type], int_type))
int_type.attrs.add("__mul__", func([int_type], int_type))
int_type.attrs.add("__truediv__", func([int_type], float_type))
int_type.attrs.add("__floordiv__", func([int_type], int_type))
int_type.attrs.add("__mod__", func([int_type], int_type))
int_type.attrs.add("__pow__", func([int_type], union(int_type, float_type)))
int_type.attrs.add("__lshift__", func([int_type], int_type))
int_type.attrs.add("__rshift__", func([int_type], int_type))
int_type.attrs.add("__and__", func([int_type], int_type))
int_type.attrs.add("__or__", func([int_type], int_type))
int_type.attrs.add("__xor__", func([int_type], int_type))

int_type.attrs.add("__neg__", func([], int_type))
int_type.attrs.add("__pos__", func([], int_type))
int_type.attrs.add("__abs__", func([], int_type))
int_type.attrs.add("__invert__", func([], int_type))

int_type.attrs.add("__eq__", func([int_type], bool_type))
int_type.attrs.add("__ne__", func([int_type], bool_type))
int_type.attrs.add("__lt__", func([int_type], bool_type))
int_type.attrs.add("__le__", func([int_type], bool_type))
int_type.attrs.add("__gt__", func([int_type], bool_type))
int_type.attrs.add("__ge__", func([int_type], bool_type))

_int_or_none = union(int_type, none_type)

str_type = class_type("str")
str_type.attrs.add("__eq__", func([str_type], bool_type))
str_type.attrs.add("find", func([str_type], int_type))
str_type.attrs.add("replace", func([str_type, str_type], str_type))
str_type.attrs.add("format", overloaded_func(
    func([object_type], str_type),
    func([object_type, object_type], str_type),
    func([object_type, object_type, object_type], str_type),
    func([object_type, object_type, object_type, object_type], str_type),
))

str_meta_type = meta_type(str_type, [
    attr("__call__", func([any_type], str_type)),
])

bool_meta_type = meta_type(bool_type, [
    attr("__call__", func([any_type], bool_type)),
])

iterator = generic_structural_type("iterator", [covariant("T")], lambda T: [
    attr("__iter__", func([], iterator(T))),
    attr("__next__", func([], T)),
])

iterable = generic_structural_type("iterable", [covariant("T")], lambda T: [
    attr("__iter__", func([], iterator(T))),
])
str_type.attrs.add("join", func([iterable(str_type)], str_type))

has_len = structural_type("has_len")
has_len.attrs.add("__len__", func([], int_type))

slice_type = generic_class(
    "slice",
    [covariant("A"), covariant("B"), covariant("C")],
    lambda A, B, C: [
        attr("start", A),
        attr("stop", B),
        attr("step", C),
    ]
)

list_type = generic_class("list", ["T"], lambda T: [
    attr("__setitem__", func([int_type, T], none_type)),
    attr("__iter__", func([], iterator(T))),
    attr("__contains__", func([object_type], bool_type)),
    attr("__len__", func([], int_type)),
    attr("append", func([T], none_type)),
    attr("__getitem__", overloaded_func(
        func([int_type], T),
        func([slice_type(_int_or_none, _int_or_none, _int_or_none)], list_type(T)),
    )),
    attr("__add__", func([list_type(T)], list_type(T))),
    attr("pop", func([], T)),
])

list_meta_type = meta_type(list_type, [
    attr("__call__", generic_func(["T"], lambda T: func([iterable(T)], list_type(T)))),
])

dict_type = generic_class("dict", ["K", "V"], lambda K, V: [
    attr("__eq__", func([object_type], bool_type)),
    attr("__getitem__", func([K], V)),
    attr("__setitem__", func([K, V], none_type)),
    attr("__iter__", func([], iterator(K))),
    attr("get", func([K, V], V)),
    attr("keys", func([], iterator(K))),
    attr("items", func([], iterator(tuple_type(K, V)))),
    attr("copy", func([], dict_type(K, V))),
])

dict_meta_type = meta_type(dict_type)

exception_type = class_type("Exception")
exception_meta_type = meta_type(exception_type, [
    attr("__call__", func([str_type], exception_type)),
])

traceback_type = class_type("traceback")

assertion_error_type = class_type("AssertionError", base_classes=[exception_type])
assertion_error_meta_type = meta_type(assertion_error_type, [
    attr("__call__", func([str_type], assertion_error_type)),
])

stop_iteration_type = class_type("StopIteration", base_classes=[exception_type])
stop_iteration_meta_type = meta_type(stop_iteration_type, [
    attr("__call__", func([], stop_iteration_type)),
])

def _create_tuple_class(length):
    return generic_class(
        "tuple{}".format(length),
        [chr(ord("A") + index) for index in range(length)]
    )

_tuple_types = [_create_tuple_class(index) for index in range(0, 10)]

def tuple_type(*args):
    return _tuple_types[len(args)](*args)


def is_tuple(type_):
    return any(
        tuple_type.is_instantiated_type(type_)
        for tuple_type in _tuple_types
    )
