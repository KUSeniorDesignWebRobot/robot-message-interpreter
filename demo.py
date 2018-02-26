import json
import time
import signal
import sys

from Interpreter import Interpreter, InterpreterException
from Actuator import Actuator
from ManifestReader import ManifestReader

interpreter = None

# TODO: use manifest reader to import manifest and generate list of actuators


def handle_signal(signal, frame):
        print('You can also enter "q", "quit", or "exit" to quit')
        print('Exiting...')
        if interpreter is not None:
            interpreter.stop()
        sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)


def main():
    # TODO: change lots of stuff
    pass
    # global interpreter
    # pp = PrettyPrinter()

    # # shorthand way of creating a list of MockActuators using keyword args specified in actuatorList
    # actuators = [MockActuator(**a) for a in actuatorList]
    # interpreter = Interpreter(actuators)
    # while True:
    #     print("Current state:", pp.pformat(interpreter.actuatorRecords))
    #     messageStr = str(input("message: "))
    #     if messageStr in ["q", "quit", "exit"]:
    #         interpreter.stop()
    #         break
    #     if messageStr != "":
    #         message = json.loads(messageStr)
    #         if "timestamp" not in message:
    #             message["timestamp"] = time.time()
    #         interpreter.interpret(message)


if __name__ == "__main__":
    main()
