class ServoMessage:

    def __init__(self, manager):
        self.manager = manager
    
    def build(self, channel, value, speed=None, time=None):
        self.channel = channel
        self.value = value
        self.speed = speed
        self.time = time

    def send(self):
        self.manager.enqueue(self)

    def __str__(self):
        return str({
        "channel": self.channel,
        "value": self.value,
        "speed": self.speed,
        "time": self.time
    })