from .types import (
    scalar_type, meta_type, union, structural_type, generic_structural_type,
    generic_class, func, overloaded_func,
    attr,
    any_type, object_type,
    covariant,
)

none_type = scalar_type("NoneType")

boolean_type = scalar_type("bool")

int_type = scalar_type("int")

float_type = scalar_type("float")

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

int_type.attrs.add("__eq__", func([int_type], boolean_type))
int_type.attrs.add("__ne__", func([int_type], boolean_type))
int_type.attrs.add("__lt__", func([int_type], boolean_type))
int_type.attrs.add("__le__", func([int_type], boolean_type))
int_type.attrs.add("__gt__", func([int_type], boolean_type))
int_type.attrs.add("__ge__", func([int_type], boolean_type))

_int_or_none = union(int_type, none_type)

str_type = scalar_type("str")
str_type.attrs.add("find", func([str_type], int_type))

str_meta_type = meta_type(str_type, [
    attr("__call__", func([any_type], str_type)),
])

bool_meta_type = meta_type(boolean_type, [
    attr("__call__", func([any_type], boolean_type)),
])

iterator = generic_structural_type("iterator", [covariant("T")])
iterator.attrs.add("__iter__", lambda T: func([], iterator(T)))
iterator.attrs.add("__next__", lambda T: func([], T))

iterable = generic_structural_type("iterable", [covariant("T")])
iterable.attrs.add("__iter__", lambda T: func([], iterator(T)))

has_len = structural_type("has_len")
has_len.attrs.add("__len__", func([], int_type))

slice_type = generic_class("slice", [covariant("A"), covariant("B"), covariant("C")], {
    attr("start", lambda A, B, C: A),
    attr("stop", lambda A, B, C: B),
    attr("step", lambda A, B, C: C),
})

list_type = generic_class("list", ["T"], [
    attr("__setitem__", lambda T: func([int_type, T], none_type)),
    attr("__iter__", lambda T: func([], iterator(T))),
    attr("__contains__", lambda T: func([object_type], boolean_type)),
    attr("append", lambda T: func([T], none_type)),
])
list_type.attrs.add(
    "__getitem__",
    lambda T: overloaded_func(
        func([int_type], T),
        func([slice_type(_int_or_none, _int_or_none, _int_or_none)], list_type(T)),
    ),
)

list_meta_type = meta_type(list_type)

dict_type = generic_class("dict", ["K", "V"], [
    attr("__getitem__", lambda K, V: func([K], V)),
    attr("__setitem__", lambda K, V: func([K, V], none_type)),
    attr("__iter__", lambda K, V: func([], iterator(K))),
])

dict_meta_type = meta_type(dict_type)

exception_type = scalar_type("Exception")
exception_meta_type = meta_type(exception_type, [
    attr("__call__", func([str_type], exception_type)),
])

traceback_type = scalar_type("traceback")

assertion_error_type = scalar_type("AssertionError", base_classes=[exception_type])
assertion_error_meta_type = meta_type(assertion_error_type, [
    attr("__call__", func([str_type], assertion_error_type)),
])


def _create_tuple_class(length):
    return generic_class(
        "tuple{}".format(length),
        [chr(ord("A") + index) for index in range(length)]
    )

_tuple_types = [_create_tuple_class(index) for index in range(0, 10)]

def tuple_type(*args):
    return _tuple_types[len(args)](*args)

