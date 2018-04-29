"""
Basic mock class for a robotic actuator
Does not store significant amounts of metadata about the actuator as this should be managed in the interpreter
"""
import logging
import uuid



class MockActuator:
    def __init__(self,
                 channel=None,
                 valueRange={"gte": -1, "lte": 1},
                 defaultValue=0,
                 expirationBehavior="dynamic",
                 _id=None):
        if _id is None:
            self.uuid = uuid.uuid4()
        else:
            self.uuid = uuid.UUID(_id)
        self.range = valueRange
        self.value = defaultValue
        self.defaultValue = defaultValue
        self.expirationBehavior = expirationBehavior

    def __str__(self):
        obj = {
            "uuid": self.uuid,
            "value": self.value,
            "range": self.range
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
            self._value = value
        else:
            # This situation should always be prevented by the interpeter
            raise Exception("Value %d is not within acceptable range for actuator %s" % (value, self.uuid))
