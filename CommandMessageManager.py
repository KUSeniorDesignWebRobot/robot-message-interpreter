from MessengerRD import Messenger, OfflineServerError
import config
# from Interpreter import Interpreter
from MockActuator import MockActuator
import time
import uuid
import logging
import threading
# from ReportMessageGenerator import ReportMessageGenerator
from Interpreter import Interpreter, InterpreterException
from Actuator import Actuator
# from MockActuator import MockActuator
from ManifestReader import ManifestReader
import config

myDummyActuatorList = [
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


def commandMessageManager(manifest):
    # TODO: use manifest reader to import manifest and generate list of actuators
    #manifest.setVar('testing', True)

    actuator_specifications = manifest['actuators']
    actuators = []
    for spec in actuator_specifications:
        actuators.append(Actuator(**{
            "channel": spec["channel"],
            "_id": spec["_id"],
            "valueRange": spec["valueRange"],
            "expirationBehavior": spec["expirationBehavior"],
            "defaultValue": spec["defaultValue"],
            "mock": config.MOCK
        }))

    interpreter = Interpreter(actuators)
    with Messenger("command", "acknowledgement", manifest) as m:
        try:
            if(m.send_handshake()):
                while m.isConnected():
                    time.sleep(0.02)
                    reply = m.recv()
                    if(reply):
                        print("I: Server replied with message (%s)" % reply)
                        # last_timestamp = time.time()
                        last_message_id = reply["message_id"]
                        if(reply["message_type"] == "command"):
                            parsed_dict = {"message_id": reply["message_id"], "message_type": reply["message_type"],
                                           "robot_id": reply["robot_id"], "configuration_id": reply["configuration_id"],
                                           "session_id": reply["session_id"], "timestamp": reply["timestamp"],
                                           "instructions": list()}
                            for i in reply["instructions"]:
                                parsed_dict["instructions"].append(i)
                            print("Send to Interpreter")
                            interpreter.interpret(parsed_dict)
                            print("Interpreter sent message")
                            print("SENDING Acknowledgement")
                            request = {"message_id": last_message_id, "message_type": "acknowledgement","timestamp": time.time()}
                            m.send(request)
                else:
                    print("Exiting")
        except KeyboardInterrupt:
            print("Exiting")
    interpreter.stop()
