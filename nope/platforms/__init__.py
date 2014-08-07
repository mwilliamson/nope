from . import nodejs, python


def find_platform_by_name(platform_name):
    return _platforms[platform_name]


_all = [
    python.Python2(),
    python.Python3(),
    nodejs.NodeJs(),
]


_platforms = dict((platform.name, platform) for platform in _all)
