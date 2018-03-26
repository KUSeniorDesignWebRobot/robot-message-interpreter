from Messenger import Messenger, OfflineServerError
import config
from Interpreter import Interpreter
from MockActuator import MockActuator
import time
from uuid import UUID
import logging
import threading
from ReportMessageGenerator import ReportMessageGenerator

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


def commandMessageManager(actuatorList):
    actuators = [MockActuator(**a) for a in actuatorList]
    interpreter = Interpreter(actuators)
    #initialize first acknowledgement message_id and timestamp
    #this valid UUID of zeros indicates the opening of the connection to the robot
    #TODO The all-zero UUID is actually invalid.  Need to designate a dummy default UUID value.
    #Maybe just random like a normal message?
    last_message_id = "e1b97e17-9cd3-4361-9df3-04db98d0c829"
    last_timestamp = time.time()
    with Messenger("command", "acknowledgement") as m:
        retries_left = config.REQUEST_RETRIES
        #Example Termination Message
        tM = {
              "message_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
              "message_type": "termination",
              "timestamp": 1509748526.3482552
        }
        while retries_left > 0:
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
                        if(reply["message_type"] == "command"):
                            parsed_dict = {"message_id": reply["message_id"], "message_type": reply["message_type"],
                                           "robot_id": reply["robot_id"], "configuration_id": reply["configuration_id"],
                                           "session_id": reply["session_id"], "timestamp": reply["timestamp"],
                                           "instructions": list()}
                            for i in reply["instructions"]:
                                parsed_dict["instructions"].append(i)

                            # ###### CALL INTERPRETTER PASSING parsedDict - PLEASE CORRECT IF WRONG, don't know how its structured ######
                            interpreter.interpret(parsed_dict)
                        # elif(reply["message_type"] == "termination"):
                        #     print("Termination Message Received, Exiting!")
                        #     while(True):
                        #         print("waiting")
                        #     break
                        retries_left = config.REQUEST_RETRIES
                        expect_reply = False

                    else:
                        try:
                            retries_left = m.try_resend(request, retries_left)
                            if(retries_left <= 0):
                                expect_reply = False
                        # except OfflineServerError:
                        #     print("THE SERVER WAS OFFLINE!!!!!")
                        except:
                            pass

                            # break
            except KeyboardInterrupt:
                print(type(m))
                # while(True):
                #     print(type(m))
                # if (expect_reply):
                #     print("HOLD ON, I'M EXPECTING A REPLY REAL QUICK!")
                #     reply = m.recv()
                print("Exiting")
                retries_left = 0
        # m.send_termination()
    print("GOT HERE!")
    interpreter.stop()

def reportMessageManager():
    #initialize first acknowledgement message_id and timestamp
    #this valid UUID of zeros indicates the opening of the connection to the robot
    #TODO The all-zero UUID is actually invalid.  Need to designate a dummy default UUID value.
    #Maybe just random like a normal message?
    # with Messenger("acknowledgment", "report") as m:
    #     retries_left = config.REQUEST_RETRIES
    rmg = ReportMessageGenerator()
    print(rmg.is_fresh)
    while retries_left:
        try:
            print("SENDING Report")
            while(not rmg.is_fresh):
                pass
            request = rmg.current_message
            rmg.is_fresh = False
            m.send(request)
            expect_reply = True
            while expect_reply:
                if m.is_current():
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
                    # parsed_dict = {"message_id": reply["message_id"], "message_type": reply["message_type"],
                    #                "robot_id": reply["robot_id"], "configuration_id": reply["configuration_id"],
                    #                "session_id": reply["session_id"], "timestamp": reply["timestamp"],
                    #                "instructions": list()}
                    # for i in reply["instructions"]:
                    #     parsed_dict["instructions"].append(i)
                    #
                    # # ###### CALL INTERPRETTER PASSING parsedDict - PLEASE CORRECT IF WRONG, don't know how its structured ######
                    # interpreter.interpret(parsed_dict)

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


#reportMessageManager()
commandMessageManager(myDummyActuatorList)
