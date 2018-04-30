# Author: Paul McELroy
# Class for Command Messages
import logging
from uuid import UUID
import json
from pprint import PrettyPrinter

class CommandMessage:
    def __init__(self, message):
        self.message = ""
        if isinstance(message, str) and self.__is_json(message):
            message = json.loads(message)
        elif not isinstance(message, dict):
            raise Exception("Input is not a str or a json (dict) object")
            logging.error("Input is not a str or a json (dict) object")
        if self.__valid(message):
            self.message = message
        else:
            raise Exception("Command Message is not Valid")
            logging.error("Command Message is not Valid")

    def __str__(self):
        pp = PrettyPrinter()
        return (pp.pformat(self.message))

    def __repr__(self):
        return 'CommandMessage(%r)' % (self.message)

    def json(self):
        return self.message

    def str(self):
        return json.dumps(self.message)

    def __is_json(self, json_string):
        answer = True
        try:
            json_object = json.loads(json_string)
        except (ValueError):
            print("VALUE ERROR")
            logging.error("Value from JSON invalid!!")
            answer = False
        except (TypeError):
            print("TYPE ERROR")
            logging.error("Type error from JSON!!")
            answer = False
        return answer

    def __versionUUID(self, uuid_string):
        try:
            return UUID(uuid_string).version
        except ValueError:
            return None

    def __validInstruction(self, instruction):
        valid = True

        if (valid and 'actuator_id' in instruction):
            version = self.__versionUUID(instruction['actuator_id'])
            if version:
                logging.info("Message has valid actuator ID")
                pass
            else:
                raise Exception("Message has invalid actuator ID")
                logging.error("Message has invalid actuator ID ")
                valid = False
        else:
            raise Exception("Message missing actuator ID")
            logging.error("Message missing actuator ID")
            valid = False

        if (valid and 'ttl' in instruction):
            valid = isinstance(instruction['ttl'], int) or isinstance(instruction['ttl'], float)
            if valid:
                logging.info("Message has valid ttl")
                pass
            else:
                raise Exception("Message has invalid ttl type")
                logging.error("Message has invalid ttl type")
        else:
            raise Exception("Message missing ttl")
            logging.error("Message missing ttl")
            valid = False

        if (valid and 'type' in instruction):
            mType = instruction['type']
            valid  = mType  == 'dynamic' or mType  ==  'static'
            if valid:
                logging.info("Instruction has valid  type")
                pass
            else:
                raise Exception("Instruction has invalid message type")
                logging.error("Instruction has invalid message type")
        else:
            raise Exception("Instruction missing message type")
            logging.error("Instruction missing message type")
            valid = False

        if (valid and 'value' in instruction):
            valid = isinstance(instruction['value'], int) or isinstance(instruction['value'], float)
            if valid:
                logging.info("Instruction has valid value")
                pass
            else:
                raise Exception("Instruction has invalid value type")
                logging.error("Instruction has invalid value type")
        else:
            raise Exception("Instruction missing value")
            logging.error("Instruction missing value")
            valid = False
        return valid

    def __valid(self, message):
        valid = True

        if ('message_id' in message):
            version = self.__versionUUID(message['message_id'])
            logging.info(version)
            if version:
                logging.info("Message has valid message ID")
                pass
            else:
                raise Exception("Message has invalid message ID")
                logging.error("Message has invalid message ID")
                valid = False
        elif(valid):
            raise Exception("Message missing message ID")
            logging.error("Message missing message ID")
            valid = False

        if (valid and 'message_type' in message):
            mType = message['message_type']
            valid  = mType  == 'command'# or mType  ==  'report' or mType  ==  'termination'
            if valid:
                # print("Message has valid message type")
                pass
            else:
                raise Exception("Command Message has invalid message type")
        elif(valid):
            raise Exception("Message missing message type")
            valid = False

        if (valid and 'robot_id' in message):
            version = self.__versionUUID(message['robot_id'])
            if version:
                logging.info("Message has valid robot ID")
                pass
            else:
                raise Exception("Message has invalid robot ID")
                logging.error("Message has invalid robot ID")
                valid = False
        elif(valid):
            raise Exception("Message missing robot ID")
            logging.error("Message missing robot ID")
            valid = False

        if (valid and 'configuration_id' in message):
            version = self.__versionUUID(message['configuration_id'])
            if version:
                logging.info("Message has valid configuration ID")
                pass
            else:
                raise Exception("Message has invalid configuration ID")
                logging.error("Message has invalid configuration ID")
                valid = False
        elif(valid):
            raise Exception("Message missing configuration ID")
            logging.error("Message missing configuration ID")
            valid = False

        if (valid and 'session_id' in message):
            version = self.__versionUUID(message['session_id'])
            if version:
                logging.info("Message has valid session ID")
                pass
            else:
                raise Exception("Message has invalid session ID")
                logging.error("Message has invalid session ID")
                valid = False
        elif(valid):
            raise Exception("Message missing session ID")
            logging.error("Message missing session ID")
            valid = False

        if (valid and 'timestamp' in message):
            valid = isinstance(message['timestamp'], (int, float))
            if valid:
                logging.info("Message has valid timestamp")
                pass
            else:
                raise Exception("Message has invalid timestamp type")
                logging.error("Message has invalid timestamp type")
        elif(valid):
            raise Exception("Message missing timestamp")
            logging.error("Message missing timestamp")
            valid = False

        if (valid and 'instructions' in message):
            valid = isinstance(message['instructions'], list)
            if valid:
                valid = all(self.__validInstruction(instruction) for instruction in message['instructions'])
                if valid:
                    pass
                else:
                    raise Exception("Some instructions in message are invalid.")
                    logging.error("Some instructions in message are invalid.")
        elif(valid):
            raise Exception("Message has invalid instruction type.")
            logging.error("Message has invalid instruction type.")
            valid = False

        return valid

# # command message example
# # unique identifier for this message (unique within the scope of this session)
# message_id: B623211925DC
# message_type: command
# # unique identifier for the messsage recipient (id for the robot, persistent to the robot)
# robot_id: 10385E45745C
# # unique identifier for the configuration
# configuration_id: 1212FE080B15
# # unique id for this connection session
# session_id: 77AA0D3AE0C7
#
# # message authentication code
# # https://en.wikipedia.org/wiki/Message_authentication_code
# mac: 50BBD3A0F62F8DB362255240
#
# # ISO formatted timestamp of when message is issued
# timestamp: 2017-10-04T18:07:24.101908
#
# instructions:
#     - actuator_id: 6CA76E92960A
#       # time-to-live of instruction in ms
#       # essentially the instruction duration.  Instruction is invalid when superceded by more recent
#       # instruction or when ttl expires
#       ttl: 500
#       # message type determines what happens when there is no valid command for an actuator
#       # static types revert to a default value (often 0)
#       # dynamic types remain at the last command value
#       type: static
#       value: 63.45
#     - actuator_id: DCCF1DD29613
#       ttl: 500
#       type: dynamic
#       value: -32.3
#     - actuator_id: 88DB7C95F0E2
#       ttl: 250
#       type: dynamic
#       value: 0.7347
