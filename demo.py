import json
import logging
import time
import signal
import sys
from pprint import PrettyPrinter

from Interpreter import Interpreter, InterpreterException
from Actuator import Actuator
from MockActuator import MockActuator
from ManifestReader import ManifestReader

interpreter = None

# TODO: use manifest reader to import manifest and generate list of actuators
manifest = ManifestReader('manifest.json')
#manifest.setVar('testing', True)

actuator_specifications = manifest.getManifestValue('actuators')
actuators = []
for spec in actuator_specifications:
    # print({
    #     "channel": spec["channel"],
    #     "_id": spec["_id"],
    #     "valueRange": spec["valueRange"],
    #     "expirationBehavior": spec["expirationBehavior"],
    #     "defaultValue": spec["defaultValue"]
    # })
    actuators.append(Actuator(**{
        "channel": spec["channel"],
        "_id": spec["_id"],
        "valueRange": spec["valueRange"],
        "expirationBehavior": spec["expirationBehavior"],
        "defaultValue": spec["defaultValue"],
        "mock": False
    }))


interpreter = Interpreter(actuators)


def main():
    global interpreter
    pp = PrettyPrinter()

    if len(sys.argv) != 2:
        raise Exception("No source filename given")
    with open(sys.argv[1]) as sourceFile:
        dataraw = json.loads(sourceFile.read())

    # flatten from list of command messages into list of instructions
    data = []
    for d in dataraw:
        data += d["instructions"]

    startTimestamp = data[0]["timestamp"]
    last = startTimestamp
    for sample in data:
        print("Current state:", pp.pformat(interpreter.actuatorRecords))
        time.sleep(sample["timestamp"] - last)
        last = sample["timestamp"]
        message = {"instructions": [sample], "timestamp": time.time()}
        interpreter.interpret(message)

    # while True:
    #     print("Current state:", pp.pformat(interpreter.actuatorRecords))
    #     messageStr = str(input("message: "))
    #     if messageStr in ["q", "quit", "exit"]:
    #         interpreter.stop()
    #         actuators[0].servoMessageManager.stop()
    #         break
    #     if messageStr != "":
    #         message = json.loads(messageStr)
    #         if "timestamp" not in message:
    #             message["timestamp"] = time.time()
    #         interpreter.interpret(message)


def handle_signal(signal, frame):
        print('You can also enter "q", "quit", or "exit" to quit')
        print('Exiting...')
        if interpreter is not None:
            interpreter.stop()
            actuators[0].servoMessageManager.stop()
        sys.exit(0)


signal.signal(signal.SIGINT, handle_signal)

if __name__ == "__main__":
    main()
