import json
import time
import sys
from pprint import PrettyPrinter

from MockActuator import MockActuator
from Interpreter import Interpreter


actuatorList = [
    {
        "_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
        "valueRange": {
            "gte": -1,
            "lte": 1
        },
        "expirationBehavior": "static",
        "defaultValue": 0
    },
    {
        "_id": "e1b97e17-9cd3-4361-9df3-04db98d0c829",
        "valueRange": {
            "gte": -1,
            "lte": 1
        },
        "expirationBehavior": "static",
        "defaultValue": 0
    }
]


def main():
    pp = PrettyPrinter()
    actuators = [MockActuator(**a) for a in actuatorList]
    interpreter = Interpreter(actuators)
    if len(sys.argv) != 2:
        raise Exception("No source filename given")
    with open(sys.argv[1]) as sourceFile:
        data = json.loads(sourceFile.read())
    startTimestamp = data[0]["timestamp"]
    last = startTimestamp
    proc = []
    for sample in data:
        print("Current state:", pp.pformat(interpreter.actuatorRecords))
        time.sleep(sample["timestamp"] - last)
        last = sample["timestamp"]
        message = {"instructions": [sample], "timestamp": time.time()}
        print("message: %s" % (pp.pformat(sample)))
        proc.append(message)
        interpreter.interpret(message)
    print(json.dumps(proc))


if __name__ == "__main__":
    main()
