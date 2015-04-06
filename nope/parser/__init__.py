import ast
import io

from . import transform
from .typing import parse_notes
from .. import nodes


def parse(source, filename=None):
    if source.startswith("#:nope treat-as-empty"):
        return nodes.module([])
    try:
        notes = parse_notes(io.StringIO(source))
        note_seeker = NoteSeeker(notes)
        
        python_ast = ast.parse(source)
        is_executable = source.startswith("#!/")
        nope_node = transform.python_to_nope(python_ast, note_seeker, is_executable=is_executable, filename=filename)
        if notes.explicit_types:
            error = SyntaxError("explicit type is not valid here")
            (error.lineno, error.offset), _ = next(iter(notes.explicit_types.values()))
            raise error
        return nope_node
    except SyntaxError as error:
        error.filename = filename
        raise error


class NoteSeeker(object):
    def __init__(self, notes):
        self._explicit_types = notes.explicit_types
        self._type_definitions = notes.type_definitions
        self._generics = notes.generics
        self._fields = notes.fields
    
    def consume_explicit_type(self, lineno, col_offset):
        return self._consume(self._explicit_types, lineno, col_offset)
    
    def consume_type_definition(self, lineno, col_offset):
        return self._consume(self._type_definitions, lineno, col_offset)
    
    def consume_generic(self, lineno, col_offset):
        return self._consume(self._generics, lineno, col_offset)
    
    def consume_field(self, lineno, col_offset):
        return self._consume(self._fields, lineno, col_offset)
    
    def _consume(self, values, lineno, col_offset):
        return values.pop((lineno, col_offset), (None, None))[1]
