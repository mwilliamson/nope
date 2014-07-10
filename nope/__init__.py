import collections
import ast


def check(path):
    with open(path) as source_file:
        source = source_file.read()
        try:
            ast.parse(source)
        except SyntaxError:
            return Result(is_valid=False)
    return Result(is_valid=True)


Result = collections.namedtuple("Result", ["is_valid"])
