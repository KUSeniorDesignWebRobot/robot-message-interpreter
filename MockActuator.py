"""
Basic mock class for a robotic actuator
Does not store significant amounts of metadata about the actuator as this should be managed in the interpreter
"""

import uuid


class MockActuator:
    def __init__(self,
                 value_range={"gte": -1, "lte": 1},
                 initial_value=0):
        self.uuid = uuid.uuid4()
        self.range = value_range
        self.value = initial_value

    def __str__(self):
        obj = {
            "uuid": self.uuid,
            "value": self.value,
            "range": self.range
        }
        return str(obj)

    def _acceptableValue(self, value):
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
        if self._acceptableValue(value):
            self._value = value
        else:
            # This situation should always be prevented by the interpeter
            raise Exception("Value %d is not within acceptable range for actuator %s" % (value, self.uuid))
