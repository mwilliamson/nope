import os
import shutil

from ..walk import walk_tree

from . import nodejs, python


def find_platform_by_name(platform_name):
    return platforms[platform_name]


_all = [
    python.Python2(),
    python.Python3(),
    nodejs.NodeJs(),
]


platforms = dict((platform.name, platform) for platform in _all)
