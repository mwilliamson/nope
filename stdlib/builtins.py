#:generic T
class slice(object):
    #:: Self, T, T, T -> none
    def __init__(self, start, stop, step):
        self.start = start
        self.stop = stop
        self.step = step


class range(object):
    #:: Self, int, int -> none
    def __init__(self, start, end):
        self._index = start
        self._end = end
    
    #:: Self -> Self
    def __iter__(self):
        return self
    
    #:: Self -> int
    def __next__(self):
        if self._index < self._end:
            value = self._index
            self._index = self._index + 1
            return value
        else:
            raise StopIteration()
