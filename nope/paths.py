import os


def find_files(path):
    if not os.path.exists(path):
        raise IOError("{}: No such file or directory".format(path))
    elif os.path.isfile(path):
        yield path
    else:
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                yield os.path.abspath(os.path.join(root, filename))
