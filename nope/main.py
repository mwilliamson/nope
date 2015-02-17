import argparse

import nope
from nope import textseek, platforms
from nope.inference import ephemeral


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True
    
    for command in _commands:
        subparser = subparsers.add_parser(command.name)
        subparser.set_defaults(func=command.execute)
        command.create_parser(subparser)
        
    args = parser.parse_args()
    exit(args.func(args) or 0)


class CheckCommand(object):
    name = "check"
    
    @staticmethod
    def create_parser(parser):
        parser.add_argument("path", nargs="+")
    
    @staticmethod
    def execute(args):
        result = nope.check(args.path)
        if not result.is_valid:
            _print_error(result.error)
            return 1


class CompileCommand(object):
    name = "compile"
    
    @staticmethod
    def create_parser(parser):
        parser.add_argument("path")
        parser.add_argument("--backend", required=True, choices=platforms.names())
        parser.add_argument("--output-dir", required=True)
    
    @staticmethod
    def execute(args):
        nope.compile(args.path, args.output_dir, args.backend)


_commands = [
    CheckCommand,
    CompileCommand,
]

def _print_error(error):
    if isinstance(error, SyntaxError):
        _print_location(error)
        print()
        print("{}: {}".format(type(error).__name__, error.msg))
    elif hasattr(error, "node"):
        node = ephemeral.root_node(error.node)
        location = getattr(node, "location", None)
        if location is not None:
            _print_location(location)
        print(error)
    else:
        print(error)
    

def _print_location(location):
    print("File '{}', line {}, col {}".format(location.filename, location.lineno, location.offset))
    print()
    with open(location.filename) as source_file:
        print("  " + textseek.seek_line(source_file, location.lineno))
    print(" " * (2 + location.offset) + "^")
