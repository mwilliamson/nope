import collections

from . import inference, parser, compilers


def check(path):
    with open(path) as source_file:
        source = source_file.read()
        try:
            nope_ast = parser.parse(source)
        except SyntaxError as error:
            return Result(is_valid=False, error=error, value=None)
    
    try:
        inference.check(nope_ast)
    except inference.TypeCheckError as error:
        return Result(is_valid=False, error=error, value=None)
    
    return Result(is_valid=True, error=None, value=nope_ast)


def compile(source, destination_dir, platform):
    nope_ast = check(source)
    
    if not nope_ast.is_valid:
        raise nope_ast.error
    
    compilers.compile(source, nope_ast.value, destination_dir, platform)


Result = collections.namedtuple("Result", ["is_valid", "error", "value"])
