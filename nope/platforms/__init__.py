from . import nodejs, python, dotnet


def find_platform_by_name(platform_name):
    return _platforms[platform_name]


def names():
    return _platforms.keys()


_all = [
    python.Python3,
    nodejs.NodeJs,
    dotnet.DotNet,
]


_platforms = dict((platform.name, platform) for platform in _all)
