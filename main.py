import json
from pprint import PrettyPrinter

from MockActuator import MockActuator
from Interpreter import Interpreter


def main():
    pp = PrettyPrinter()
    actuators = [MockActuator() for i in range(0, 5)]
    interpreter = Interpreter(actuators)
    while True:
        # interpreter.publish()
        print("Current state:", pp.pformat(interpreter.actuatorValues))
        messageStr = str(input("message: "))
        message = json.loads(messageStr)
        interpreter.interpret(message)


if __name__ == "__main__":
    main()
