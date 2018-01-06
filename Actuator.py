"""
Does not store significant amounts of metadata about the actuator as this should be managed in the interpreter
"""

import uuid
import serial

from ServoMessageManager import ServoMessageManager

class Actuator:
    def __init__(self,
                 channel,
                 valueRange={"gte": -1, "lte": 1},
                 defaultValue=0,
                 expirationBehavior="dynamic",
                 _id=None,
                 speed=None):
        if _id is None:
            self.uuid = uuid.uuid4()
        else:
            self.uuid = uuid.UUID(_id)
        self.channel = channel
        self.range = valueRange
        self.value = defaultValue
        self.defaultValue = defaultValue
        self.expirationBehavior = expirationBehavior
        self.servoMessageManager = ServoMessageManager()
    
    def __str__(self):
        obj = {
            "uuid": self.uuid,
            "value": self.value,
            "range": self.range,
            "channel": self.channel
        }
        return str(obj)

    def acceptableValue(self, value):
        acceptable = True
        if "gt" in self.range:
            acceptable &= value > self.range["gt"]
        elif "gte" in self.range:
            acceptable &= value >= self.range["gte"]

        if "lt" in self.range:
            acceptable &= value < self.range["lt"]
        if "lte" in self.range:
            acceptable &= value <= self.range["lte"]
        return acceptable
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self.acceptableValue(value):
            # send message to servo if value was updated
            if not hasattr(self, "_value") or self._value != value:
                self._value = value
                message = self.servoMessageManager.getMessage()
                message.build(self.channel, self._value, speed=self.speed)
                message.send()
        else:
            # TODO: Interpreter should handle exception being thrown
            raise Exception("Value %d is not within acceptable range for actuator %s" % (value, self.uuid))
