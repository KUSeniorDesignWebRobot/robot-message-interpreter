"""
Does not store significant amounts of metadata about the actuator as this should be managed in the interpreter
"""
import logging
import uuid
import serial

from ServoMessageManager import ServoMessageManager


class Actuator:
    def __init__(self,
                 channel=None,
                 valueRange={"gte": -1, "lte": 1},
                 defaultValue=0,
                 expirationBehavior="dynamic",
                 _id=None,
                 speed=1000,
                 mock=True):
        if _id is None:
            self.uuid = uuid.uuid4()
        else:
            self.uuid = uuid.UUID(_id)
        self.servoMessageManager = None
        if not mock:
            self.servoMessageManager = ServoMessageManager()
        self.channel = channel
        self.range = valueRange
        self.defaultValue = defaultValue
        self.speed = speed
        self.expirationBehavior = expirationBehavior
        self.mock = mock
        self.value = defaultValue

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
    def position(self):
        # TODO: have this query value through ServoMessageManager
        return self._value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self.acceptableValue(value):
            # send message to servo if value was updated
            if not self.mock and (not hasattr(self, "_value") or self._value != value):
                self._value = value
                message = self.servoMessageManager.getMessage()
                message.build(channel=self.channel, value=self._value, speed=self.speed)
                print("Sending message: ", str(message))
                message.send()
            elif self.mock:
                self._value = value
        else:
            # TODO: Interpreter should handle exception being thrown
            raise Exception("Value %d is not within acceptable range for actuator %s" % (value, self.uuid))
