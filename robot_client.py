from Messenger import Messenger, OfflineServerError
import config
from Interpreter import Interpreter
from MockActuator import MockActuator
import time
from uuid import UUID
import threading

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
actuators = [MockActuator(**a) for a in actuatorList]
interpreter = Interpreter(actuators)

#initialize first acknowledgement message_id and timestamp
#this valid UUID of zeros indicates the opening of the connection to the robot
#TODO The all-zero UUID is actually invalid.  Need to designate a dummy default UUID value.
#Maybe just random like a normal message?
last_message_id = "e1b97e17-9cd3-4361-9df3-04db98d0c829"
last_timestamp = time.time()


print(UUID(last_message_id).version)

with Messenger("command", "acknowledgement") as m:
    retries_left = config.REQUEST_RETRIES
    while retries_left:
        try:
            # time.sleep(10)
            ######### EXAMPLE VALUES ########
            request = {"message_id": last_message_id, "message_type": "acknowledgement","timestamp": last_timestamp}
            # client.send(json.dumps(request))
            # client.send_json(request)
            print("SENDING Acknowledgement")
            m.send(request)
            expect_reply = True
            while expect_reply:
                if m.is_current():
                    commandMessage = 0
                    reply = 0
                    try:
                        reply = m.recv()
                    except:
                        print("FAILED")
                    if not reply:
                        print("NO REPLY")
                        break
                    print("I: Server replied with message (%s)" % reply)
                    last_timestamp = time.time()
                    last_message_id = reply["message_id"]
                    parsed_dict = {"message_id": reply["message_id"], "message_type": reply["message_type"],
                                   "robot_id": reply["robot_id"], "configuration_id": reply["configuration_id"],
                                   "session_id": reply["session_id"], "timestamp": reply["timestamp"],
                                   "instructions": list()}
                    for i in reply["instructions"]:
                        parsed_dict["instructions"].append(i)

                    # ###### CALL INTERPRETTER PASSING parsedDict - PLEASE CORRECT IF WRONG, don't know how its structured ######
                    interpreter.interpret(parsed_dict)

                    retries_left = config.REQUEST_RETRIES
                    expect_reply = False

                else:
                    try:
                        retries_left = m.try_resend(request, retries_left)
                    except OfflineServerError:
                        break
        except KeyboardInterrupt:
            interpreter.stop()
            break
