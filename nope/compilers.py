import shutil

from . import nodejs


def compile(source, nope_ast, destination_dir, platform):
    _compilers[platform](source, nope_ast, destination_dir)


def python2(source, nope_ast, destination_dir):
    shutil.copy(source, destination_dir)


def python3(source, nope_ast, destination_dir):
    shutil.copy(source, destination_dir)


def node(source_path, nope_ast, destination_dir):
    nodejs.nope_to_nodejs(source_path, nope_ast, destination_dir)


_compilers = {
    "python2": python2,
    "python3": python3,
    "node": node,
}
