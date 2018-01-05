import json
import time
from pprint import PrettyPrinter

from MockActuator import MockActuator
from Interpreter import Interpreter


actuatorList = [
    {
        "_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
        "valueRange": {
            "gte": 0,
            "lt": 100 
        },
        "expirationBehavior": "static",
        "defaultValue": 0
    },
    {
        "_id": "e1b97e17-9cd3-4361-9df3-04db98d0c829",
        "valueRange": {
            "gte": 0,
            "lt": 360
        },
        "expirationBehavior": "dynamic",
        "defaultValue": 180
    }
]

def main():
    pp = PrettyPrinter()
    actuators = [MockActuator(**a) for a in actuatorList]
    interpreter = Interpreter(actuators)
    while True:
        # interpreter.publish()
        print("Current state:", pp.pformat(interpreter.actuatorRecords))
        messageStr = str(input("message: "))
        if messageStr != "":
            message = json.loads(messageStr)
            if "timestamp" not in message:
                message["timestamp"] = time.time()
            interpreter.interpret(message)


if __name__ == "__main__":
    main()
