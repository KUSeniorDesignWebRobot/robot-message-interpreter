"""
Interpreter for command messages
"""

import uuid
from sched import scheduler
import time
from dateutil import parser
from datetime import datetime, timedelta

import config
from MockActuator import MockActuator


class Interpreter:
    def __init__(self, actuators):
        self.actuators = {a.uuid: a for a in actuators}
        self.actuatorValues = {a.uuid: {
            "value": a.value,
            "expires": 0}
            for a in self.actuators.values()}

    def interpret(self, message):
        """
        Accepts a command message in dict form and applies the message to the current state
        """
        # TODO: add validation of fields like robot_id, message type etc
        # TODO: add error handling for malformed messages
        # NOTE: message timestamps changed from from ISO8601 to unix epoch timestamp in seconds (with decimal milliseconds)
        message_timestamp = message["timestamp"]
        for command in message["instructions"]:
            command["adjusted_timestamp"] = float(
                message_timestamp) + (config.latency_ms / 1000)
            self.scheduleCommand(command)

    def scheduleCommand(self, command):
        """
        Accepts a command with appended "adjusted_timestamp" field and schedules it for processing when the active_timestamp is reached
        """
        # TODO: add actual scheduling
        self.apply(command)

    def apply(self, command):
        """
        Applies a command to the internal record of actuator values
        """
        actuatorUUID = uuid.UUID(command["actuator_id"])
        if actuatorUUID in self.actuators:
            # TODO: add value range checking
            self.actuatorValues[actuatorUUID
                                ]["value"] = command["value"]
            self.actuatorValues[actuatorUUID]["expires"] = datetime.utcfromtimestamp(
                command["adjusted_timestamp"] + (command["ttl"] / 1000))
        else:
            raise Exception("No matching actuator with uuid %s" %
                            (actuatorUUID))

    def publish(self):
        """
        Applies internal record of actuator values to actuators
        """
        # FIXME
        for uuid in self.actuators.keys():
            self.actuators[uuid].value = self.actuatorValues[uuid].value
