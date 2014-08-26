from . import types, name_declaration, name_resolution, name_binding, context
from .identity_dict import IdentityDict


_builtin_types = {
    "object": types.meta_type(types.object_type),
    "int": types.meta_type(types.int_type),
    "str": types.str_meta_type,
    "none": types.meta_type(types.none_type),
    "Exception": types.exception_meta_type,
    "AssertionError": types.assertion_error_meta_type,
    
    "print": types.func([types.object_type], types.none_type),
    "bool": types.func([types.object_type], types.boolean_type),
    # TODO: make abs generic e.g. T => T -> T
    "abs": types.func([types.int_type], types.int_type),
    # TODO: make divmod generic e.g. T, U where T <: DivMod[U] => T, T -> U
    "divmod": types.func([types.int_type, types.int_type], types.tuple(types.int_type, types.int_type)),
    "range": types.func([types.int_type, types.int_type], types.iterable(types.int_type)),
}


_builtin_declarations = {}
_builtin_definition_types = {}

def _setup():
    for name, type_ in _builtin_types.items():
        definition = _builtin_declarations[name] = name_declaration.VariableDeclarationNode(name)
        _builtin_definition_types[definition] = type_
    
_setup()


def references():
    return name_resolution.Context(
        declarations=_builtin_declarations,
        references=IdentityDict(),
    )

def module_context(references):
    return context.Context(references, _builtin_definition_types).enter_module()


def module_bindings(references):
    return name_binding.Context(references._references, _builtin_definition_types.copy(), set())