#:generic T
class slice(object):
    #:: Self, T, T, T -> none
    def __init__(self, start, stop, step):
        self.start = start
        self.stop = stop
        self.step = step
