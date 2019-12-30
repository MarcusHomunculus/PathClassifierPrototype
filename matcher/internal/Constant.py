# taken from https://stackoverflow.com/a/18035135
class Constant:  # use Constant(object) if in Python 2
    def __init__(self, value):
        self.value = value

    def __get__(self, *args):
        return self.value

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.value)