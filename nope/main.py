import argparse

import nope


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
        parser.add_argument("path")
    
    @staticmethod
    def execute(args):
        result = nope.check(args.path)
        if not result.is_valid:
            print(result.error)
            return 1


_commands = [
    CheckCommand
]
