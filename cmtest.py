from CommandMessage import CommandMessage as cm
import json
import logging
from pprint import PrettyPrinter
pp = PrettyPrinter()

#EXAMPLE COMMAND MESSAGE:
# {
#   "message_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
#   "message_type": "command",
#   "robot_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
#   "timestamp": 1509748526.3482552,
#   "configuration_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
#   "session_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
#   "instructions": [
#     {
#       "value": 0.10666666666666667,
#       "actuator_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
#       "ttl": 1509740686.412,
#       "type": "static"
#     },
#     {
#       "value": 0.10666666666666667,
#       "actuator_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
#       "ttl": 1509740686.412,
#       "type": "static"
#     },
#     {
#       "value": 0.10666666666666667,
#       "actuator_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
#       "ttl": 1509740686.412,
#       "type": "static"
#     }
#   ]
# }


testMsgStr = '{"message_id":"067c8c59-710a-4c15-8265-b7f1e49b828c","message_type":"command","robot_id":"067c8c59-710a-4c15-8265-b7f1e49b828c","timestamp":1509748526.3482552,"configuration_id":"067c8c59-710a-4c15-8265-b7f1e49b828c","session_id":"067c8c59-710a-4c15-8265-b7f1e49b828c","instructions":[{"value":0.10666666666666667,"actuator_id":"067c8c59-710a-4c15-8265-b7f1e49b828c","ttl":1509740686.412,"type":"static"},{"value":0.10666666666666667,"actuator_id":"067c8c59-710a-4c15-8265-b7f1e49b828c","ttl":1509740686.412,"type":"static"},{"value":0.10666666666666667,"actuator_id":"067c8c59-710a-4c15-8265-b7f1e49b828c","ttl":1509740686.412,"type":"static"}]}'

testJSON = json.loads(testMsgStr)
myMSG = cm(testMsgStr)
print("\nAs JSON (dict) object: ")
print(myMSG.json())

print("__str__ test:\n")
print(myMSG)

print("String test:\n")
print(myMSG.str())
