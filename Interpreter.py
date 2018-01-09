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

class InterpreterException(Exception):
    pass

class Interpreter:
    def __init__(self, actuators):
        # takes a list of actuators, and makes it into a dict keyed by uuid
        self.actuators = {a.uuid: a for a in actuators}
        self.actuatorRecords = {a.uuid: {"value": a.value, "defaultValue": a.defaultValue, "expires": 0,
                                         "expirationBehavior": a.expirationBehavior, "range": a.range} for a in self.actuators.values()}
        self.lock = threading.Lock()
        self.stopped = False
        self.scheduler = StateChangeScheduler(self, refreshInterval=0.200)

    def stop(self):
        """
        Shut down the interpreter safely
        """
        with self.lock:
            self.stopped = True
        self.scheduler.stop()

    def interpret(self, message):
        """
        Accepts a command message in dict form and schedules the message for application
        adjusted_timestamp of each command is set to the maximum of the message timestamp + 
        enforced latency and the current timestamp
        """
        # TODO: add validation of fields like robot_id, message type etc
        # TODO: add error handling for malformed messages
        # NOTE: message timestamps changed from from ISO8601 to unix epoch timestamp in seconds (with decimal milliseconds)
        if self.stopped:
            # reject messages after stop
            return
        
        self.scheduler.showThreads()
        self.scheduler.joinThreads()
        message_timestamp = message["timestamp"]
        for command in message["instructions"]:
            command["adjusted_timestamp"] = max(
                float(message_timestamp) + (config.latency_ms / 1000), time.time())
            self.scheduler.scheduleCommandApplication(command)

    def expire(self, _id):
        """
        Checks for expiration of an actuator record and takes appropriate action
        """
        expired = False
        with self.lock:
            actuatorRecord = self.actuatorRecords[_id]
            if actuatorRecord["expires"].timestamp() <= time.time():
                expired = True
                if actuatorRecord["expirationBehavior"] == "dynamic":
                    # take no action
                    pass
                elif actuatorRecord["expirationBehavior"] == "static":
                    actuatorRecord["value"] = actuatorRecord["defaultValue"]
                else:
                    raise InterpreterException("Undefined expiration behavior %s for actuator %s" % (
                        actuatorRecord.expirationBehavior, _id))
        if expired:
            self.publish()

    def apply(self, command):
        """
        Applies a command to the internal record of actuator values
        """
        _id = uuid.UUID(command["actuator_id"])
        if _id in self.actuators:
            with self.lock:
                self.actuatorRecords[_id]["value"] = command["value"]
                expires = datetime.fromtimestamp(
                    command["adjusted_timestamp"] + (command["ttl"] / 1000))
                self.actuatorRecords[_id]["expires"] = expires
            self.scheduler.scheduleExpiration(_id)
            self.publish()
        else:
            raise InterpreterException("No matching actuator with uuid %s" %
                            (_id))

    def publish(self):
        """
        Applies internal record of actuator values to actuators
        """
        with self.lock: 
            for _id in self.actuators.keys():
                self.actuators[_id].value = self.actuatorRecords[_id]["value"]
