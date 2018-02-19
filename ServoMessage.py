# TODO: might need two versions of servo message, a command and a query type
# both have a channel, but the query type needs to return a promise (probably as part of this)

class ServoMessage:

    def __init__(self, manager):
        self.manager = manager
        self.channel = None
        self.value = None
        self.speed = None
        self.time = None
    
    def build(self, channel, value, speed=None, time=None):
        self.channel = channel
        self.value = value
        self.speed = speed
        self.time = time

    def send(self):
        self.manager.enqueue(self)

    def asDict(self):
        return {
            "channel": self.channel,
            "value": self.value,
            "speed": self.speed,
            "time": self.time
        }

    def __str__(self):
        return str(self.asDict())
