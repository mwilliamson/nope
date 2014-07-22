import shutil


def compile(source, destination_dir, platform):
    _compilers[platform](source, destination_dir)


def python2(source, destination_dir):
    shutil.copy(source, destination_dir)


def python3(source, destination_dir):
    shutil.copy(source, destination_dir)



_compilers = {
    "python2": python2,
    "python3": python3,
}
