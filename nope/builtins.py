from . import types, name_declaration, context
from .modules import BuiltinModule


_builtin_types = {
    "object": types.meta_type(types.object_type),
    "int": types.meta_type(types.int_type),
    "str": types.str_meta_type,
    "none": types.meta_type(types.none_type),
    "list": types.list_meta_type,
    "dict": types.dict_meta_type,
    "Exception": types.exception_meta_type,
    "AssertionError": types.assertion_error_meta_type,
    
    "print": types.func([types.object_type], types.none_type),
    "bool": types.bool_meta_type,
    "len": types.func([types.has_len], types.int_type),
    # TODO: make abs generic e.g. T => T -> T
    "abs": types.func([types.int_type], types.int_type),
    # TODO: make divmod generic e.g. T, U where T <: DivMod[U] => T, T -> U
    "divmod": types.func([types.int_type, types.int_type], types.tuple_type(types.int_type, types.int_type)),
    "range": types.func([types.int_type, types.int_type], types.iterable(types.int_type)),
    
    "enumerate": types.generic_func(["T"], lambda T: types.func(
        [types.iterable(T)],
        types.iterable(types.tuple_type(types.int_type, T)),
    )),
    
    # TODO: varargs (or overload)
    "zip": types.generic_func(["T1", "T2"], lambda T1, T2: types.func(
        [types.iterable(T1), types.iterable(T2)],
        types.iterable(types.tuple_type(T1, T2))
    )),
    
    "isinstance": types.func([types.object_type], types.any_meta_type),
}


_builtin_declarations = {}
_builtin_definition_types = {}

def _setup():
    for name, type_ in _builtin_types.items():
        definition = _builtin_declarations[name] = name_declaration.VariableDeclarationNode(name)
        _builtin_definition_types[definition] = type_
    
_setup()


def declarations():
    return name_declaration.Declarations(_builtin_declarations)

def module_context(references):
    return context.Context(references, _builtin_definition_types).enter_module()


def module_bindings(references):
    return dict((declaration, True) for declaration in _builtin_declarations.values())


builtin_modules = {
    "cgi": BuiltinModule("cgi", types.module("cgi", [
        types.attr(
            "escape",
            types.func(
                [types.str_type, types.func_arg("quote", types.boolean_type, optional=True)],
                types.str_type
            ),
            read_only=True
        )
    ])),
    "collections": BuiltinModule("collections", types.module("collections", [
    ])),
    "dodge": BuiltinModule("dodge", types.module("dodge", [
    ]))
}
