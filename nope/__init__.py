import collections
import shutil

from . import inference, parser


def check(path):
    with open(path) as source_file:
        source = source_file.read()
        try:
            nope_ast = parser.parse(source)
        except SyntaxError:
            return Result(is_valid=False)
    
    try:
        inference.check(nope_ast)
    except inference.TypeCheckError:
        return Result(is_valid=False)
    
    return Result(is_valid=True)


def compile(source, destination_dir, platform):
    if platform == "python3":
        shutil.copy(source, destination_dir)


Result = collections.namedtuple("Result", ["is_valid"])
