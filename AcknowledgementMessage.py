# Author: Paul McELroy
# Class for Acknowledgement Messages

from uuid import UUID
import json
from pprint import PrettyPrinter

class AcknowledgementMessage:
    def __init__(self, message):
        self.message = ""
        if isinstance(message, str) and self.__is_json(message):
            message = json.loads(message)
        elif not isinstance(message, dict):
            raise Exception("Input is not a str or a json (dict) object")

        if self.__valid(message):
            self.message = message
        else:
            raise Exception("Acknowledgement Message is not Valid")

    def __str__(self):
        pp = PrettyPrinter()
        return (pp.pformat(self.message))

    def __repr__(self):
        return 'AcknowledgementMessage(%r)' % (self.message)

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
            answer = False
        except (TypeError):
            print("TYPE ERROR")
            answer = False
        return answer

    def __versionUUID(self, uuid_string):
        try:
            return UUID(uuid_string).version
        except ValueError:
            return None

    def __valid(self, message):
        valid = True

        if ('message_id' in message):
            version = self.__versionUUID(message['message_id'])
            # print(version)
            if version:
                # print("Message has valid message ID")
                pass
            else:
                raise Exception("Message has invalid message ID")
                valid = False
        elif(valid):
            raise Exception("Message missing message ID")
            valid = False

        if (valid and 'message_type' in message):
            mType = message['message_type']
            valid  = mType  == 'acknowledgement'
            if valid:
                # print("Message has valid message type")
                pass
            else:
                raise Exception("Acknowledgement Message has invalid message type")
        elif(valid):
            raise Exception("Message missing message type")
            valid = False


        if (valid and 'timestamp' in message):
            valid = isinstance(message['timestamp'], float)
            if valid:
                # print("Message has valid timestamp")
                pass
            else:
                raise Exception("Message has invalid timestamp type")
        elif(valid):
            raise Exception("Message missing timestamp")
            valid = False

        return valid

# # Acknowledgement message example
# # unique identifier for the message this acknowledgement message is about
# message_id: B623211925DC
# message_type: acknowledgement
#
# # ISO formatted timestamp of when message is issued
# timestamp: 2017-10-04T18:07:24.101908
