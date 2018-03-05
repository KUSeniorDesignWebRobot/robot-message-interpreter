import json
import time
from pprint import PrettyPrinter
import signal
import logging
import argparse
import sys
from MockActuator import MockActuator
from Interpreter import Interpreter

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

def handle_signal(signal, frame):
        print('You can also enter "q", "quit", or "exit" to quit')
        print('Exiting...')
        if interpreter is not None:
            interpreter.stop()
        sys.exit(0)


signal.signal(signal.SIGINT, handle_signal)

def _log_level_string_to_int(log_level_string):
    if not log_level_string in _LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(log_level_string, _LOG_LEVEL_STRINGS)
        raise argparse.ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the logging log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


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

interpreter = None

def main():
    # pass in log level via --log-level= (DEBUG or INFO or WARNING or ERROR)
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level=',
                    default='DEBUG',
                    dest='log_level',
                    type=_log_level_string_to_int,
                    nargs='?',
                    help='Set the logging output level. {0}'.format(_LOG_LEVEL_STRINGS))
    parsed_args = parser.parse_args()
    logging.basicConfig(filename='\var\log\robot.log', format='%(asctime)s:%(levelname)s:%(message)s', level=parsed_args.log_level)
    logging.debug('Started')
    logging.info('Started')
    logging.warning('Started')
    logging.error('Started')
    logging.critical('Started')
    global interpreter
    pp = PrettyPrinter()

    # shorthand way of creating a list of MockActuators using keyword args specified in actuatorList
    actuators = [MockActuator(**a) for a in actuatorList]
    interpreter = Interpreter(actuators)
    while True:
        print("Current state:", pp.pformat(interpreter.actuatorRecords))
        messageStr = str(input("message: "))
        if messageStr in ["q", "quit", "exit"]:
            interpreter.stop()
            break
        if messageStr != "":
            message = json.loads(messageStr)
            if "timestamp" not in message:
                message["timestamp"] = time.time()
            interpreter.interpret(message)
    logging.debug('Finished')
    logging.info('Finished')
    logging.warning('Finished')
    logging.error('Finished')
    logging.critical('Finished')


if __name__ == "__main__":
    main()
