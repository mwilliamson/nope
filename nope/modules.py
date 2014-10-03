class LocalModule(object):
    def __init__(self, path, node):
        self.path = path
        self.node = node


class BuiltinModule(object):
    def __init__(self, name):
        self.name = name
