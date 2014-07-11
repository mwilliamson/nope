import collections
import ast
import shutil

from . import inference, transform


def check(path):
    with open(path) as source_file:
        source = source_file.read()
        try:
            python_ast = ast.parse(source)
        except SyntaxError:
            return Result(is_valid=False)
    
    nope_ast = transform.python_to_nope(python_ast)
    try:
        inference.check(nope_ast)
    except inference.TypeCheckError:
        return Result(is_valid=False)
    
    return Result(is_valid=True)


def compile(source, destination_dir, platform):
    if platform == "python3":
        shutil.copy(source, destination_dir)


Result = collections.namedtuple("Result", ["is_valid"])
