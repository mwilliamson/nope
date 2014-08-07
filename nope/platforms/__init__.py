import os
import shutil

from ..walk import walk_tree

from . import nodejs, python


def compile(source, nope_ast, destination_dir, platform_name):
    platforms[platform_name].compile(source, nope_ast, destination_dir)



_all = [
    python.Python2(),
    python.Python3(),
    nodejs.NodeJs(),
]


platforms = dict((platform.name, platform) for platform in _all)
