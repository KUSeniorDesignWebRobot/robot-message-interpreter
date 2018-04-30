import random

class ScheduledAction:
    def __init__(self, function, timestamp, args=[], kwargs={}):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.timestamp = timestamp
        self.rand = random.random()

    def run(self):
        self.function(*self.args, **self.kwargs)

    def __cmp__(self, other):
        if self.timestamp == other.timestamp:
            return self.rand - other.rand
        else:
            return self.timestamp - other.timestamp

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0
