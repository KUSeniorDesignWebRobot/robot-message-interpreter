import time
import threading

class StateChangeScheduler:
    """
    Handles scheduling of state refresh and multithreaded timing for an Interpreter
    """

    def __init__(self, interpreter, refreshInterval):
        """
        :param Interpreter interpreter: The interpreter to run state change functions on
        :param float refreshInterval: The refresh interval for state changes in seconds
        """
        self.interpreter = interpreter
        self.refreshInterval = refreshInterval
        self.refreshTarget = time.time()
        self.intervalRefresh()

    def scheduleCommandApplication(self, command):
        """
        Accepts a command with appended "adjusted_timestamp" field and schedules it for 
        processing when the active_timestamp is reached

        :param dict command: A command with appended adjusted_timestamp to apply
        """
        delaySeconds = command["adjusted_timestamp"] - time.time()
        print(delaySeconds)
        threading.Timer(delaySeconds, self.interpreter.apply, [command]).start()

    def scheduleExpiration(self, actuatorUUID):
        """
        Checks for message expiration of the specified actuatorUUID and takes appropriate action
        :param uuid.UUID actuatorUUID: The UUID of the actuator to perform expiration validation on
        """
        actuatorRecord = self.interpreter.actuatorRecords[actuatorUUID]
        delaySeconds = actuatorRecord["expires"].timestamp() - time.time()
        print(delaySeconds)
        threading.Timer(delaySeconds, self.interpreter.expire,
                        [actuatorUUID]).start()

    def intervalRefresh(self):
        self.interpreter.publish()
        self.refreshTarget += self.refreshInterval
        delaySeconds = self.refreshTarget - time.time()
        threading.Timer(delaySeconds, self.intervalRefresh).start()
