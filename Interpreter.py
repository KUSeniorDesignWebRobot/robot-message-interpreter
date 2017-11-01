"""
Interpreter for command messages
"""

import uuid
import time
import threading
from sched import scheduler
from datetime import datetime, timedelta

import config
from StateChangeScheduler import StateChangeScheduler
from MockActuator import MockActuator


class Interpreter:
    def __init__(self, actuators):
        self.actuators = {a.uuid: a for a in actuators}
        self.actuatorRecords = {a.uuid: {"value": a.value, "defaultValue": a.defaultValue, "expires": 0,
                                         "expirationBehavior": a.expirationBehavior, "range": a.range} for a in self.actuators.values()}
        self.lock = threading.Lock()
        self.scheduler = StateChangeScheduler(self, refreshInterval=0.200)

    def interpret(self, message):
        """
        Accepts a command message in dict form and schedules the message for application
        adjusted_timestamp of each command is set to the maximum of the message timestamp + 
        enforced latency and the current timestamp
        """
        # TODO: add validation of fields like robot_id, message type etc
        # TODO: add error handling for malformed messages
        # NOTE: message timestamps changed from from ISO8601 to unix epoch timestamp in seconds (with decimal milliseconds)
        message_timestamp = message["timestamp"]
        for command in message["instructions"]:
            command["adjusted_timestamp"] = max(
                float(message_timestamp) + (config.latency_ms / 1000), time.time())
            self.scheduler.scheduleCommandApplication(command)

    def expire(self, actuatorUUID):
        """
        Checks for expiration of an actuator record and takes appropriate action
        """
        expired = False
        self.lock.acquire()
        actuatorRecord = self.actuatorRecords[actuatorUUID]
        if actuatorRecord["expires"].timestamp() <= time.time():
            expired = True
            if actuatorRecord["expirationBehavior"] == "dynamic":
                # take no action
                pass
            elif actuatorRecord["expirationBehavior"] == "static":
                actuatorRecord["value"] = actuatorRecord["defaultValue"]
            else:
                raise Exception("Undefined expiration behavior %s for actuator %s" % (
                    actuatorRecord.expirationBehavior, actuatorUUID))
        self.lock.release()
        if expired:
            self.publish()

    def apply(self, command):
        """
        Applies a command to the internal record of actuator values
        """
        actuatorUUID = uuid.UUID(command["actuator_id"])
        if actuatorUUID in self.actuators:
            # TODO: add value range checking

            self.lock.acquire()
            self.actuatorRecords[actuatorUUID
                                 ]["value"] = command["value"]
            expires = datetime.fromtimestamp(
                command["adjusted_timestamp"] + (command["ttl"] / 1000))
            self.actuatorRecords[actuatorUUID]["expires"] = expires
            self.scheduler.scheduleExpiration(actuatorUUID)
            self.lock.release()

            self.publish()
        else:
            raise Exception("No matching actuator with uuid %s" %
                            (actuatorUUID))

    def publish(self):
        """
        Applies internal record of actuator values to actuators
        """
        self.lock.acquire()
        for actuatorUUID in self.actuators.keys():
            self.actuators[actuatorUUID].value = self.actuatorRecords[actuatorUUID]["value"]
        self.lock.release()
