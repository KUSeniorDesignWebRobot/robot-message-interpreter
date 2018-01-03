"""
Basic mock class for a robotic actuator
Does not store significant amounts of metadata about the actuator as this should be managed in the interpreter
"""

import uuid
import serial



class Actuator:
    def __init__(self,
                 channel,
                 valueRange={"gte": -1, "lte": 1},
                 defaultValue=0,
                 expirationBehavior="dynamic",
                 _id=None,
                 speed=500):
        if _id is None:
            self.uuid = uuid.uuid4()
        else:
            self.uuid = uuid.UUID(_id)
        self.channel = channel
        self.range = valueRange
        self.value = defaultValue
        self.defaultValue = defaultValue
        self.expirationBehavior = expirationBehavior
    
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
            # TODO: should send message to servo with updated value if set
            if not hasattr(self, "_value") or self._value != value:
                self._value = value
                # maybe call a function that sends the servo message here?
                self.send_servo(value)
        else:
            # This situation should always be prevented by the interpeter
            raise Exception("Value %d is not within acceptable range for actuator %s" % (value, self.uuid))



    def send_servo(self, serial_conn, value):
        st_cmd = b"#{} P{} S1000\r".format(self.channel, value)
        #st_cmd = str('#7 P' + value + ' S1000\r')
        serial_conn.write(st_cmd)


if __name__ == "__main__":
    import time

    # Holds actuator objects
    myActuators = []

    # Single serial connection
    s = serial.Serial('/dev/ttyUSB0')
    if s is None:
            raise IOError("Serial Connection Failed!")

    # Instantiation
    for channel in range(16):
        testClass = Actuator(channel,
                             valueRange={"gte": 500, "lte": 2500},
                             defaultValue=1500,
                             expirationBehavior="dynamic",
                             _id=None,
                             speed=500)
        myActuators.append(testClass)

    # Dump actuator stats as they would appear in the actuator list
    for actuator in myActuators:
        print(actuator)

    testPattern = [100*x for x in range(5, 26)]

    #testPattern = []
    #for x in range(5, 26):
    #    testPattern.append(100 * x)
    
    for actuator in myActuators:
        print("Testing servo:")
        print("\t{}".format(actuator))
        # Issue test across full range of motion
        for testValue in testPattern:
            actuator.send_servo(s, testValue)
            time.sleep(0.5)
        
        # Center servo before moving on
        actuator.send_servo(s, 1500)


