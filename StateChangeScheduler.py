import time
import threading
import logging

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
        self.threads = []
        self.lock = threading.Lock()
        self.stopped = False
        self.intervalRefresh()

    def stop(self):
        print("StateChangeScheduler.stop") #TODO deleteme
        with self.lock:
            print("\tgot lock") #TODO deleteme
            self.stopped = True
        # wait for all threads to rejoin
        print("\tjoining threads") #TODO deleteme
        self.joinThreads(block=True, timeout=None)
        print("\tjoined threads") #TODO deleteme

    def showThreads(self):
        print(threading.enumerate())

    def joinThreads(self, block=False, timeout=0):
        # try to acquire lock, just skips if block is False
        print("StateChangeScheduler.joinThreads") #TODO deleteme
        if self.lock.acquire(blocking=block):
            print("\tgot lock") #TODO deleteme
            threads = list(self.threads)
            self.lock.release()
        else:
            return
        print("\tjoining ", len(threads), " threads")
        for thread in threads:
            thread.join(timeout=timeout)
            if not thread.is_alive():
                self.threads.remove(thread)

    def scheduleCommandApplication(self, command):
        """
        Accepts a command with appended "adjusted_timestamp" field and schedules it for
        processing when the active_timestamp is reached

        :param dict command: A command with appended adjusted_timestamp to apply
        """
        delaySeconds = command["adjusted_timestamp"] - time.time()
        timerthread = threading.Timer(delaySeconds, self.interpreter.apply, [command])
        timerthread.start()
        with self.lock:
            self.threads.append(timerthread)

    def scheduleExpiration(self, actuatorUUID):
        """
        Checks for message expiration of the specified actuatorUUID and takes appropriate action
        :param uuid.UUID actuatorUUID: The UUID of the actuator to perform expiration validation on
        """
        actuatorRecord = self.interpreter.actuatorRecords[actuatorUUID]
        delaySeconds = actuatorRecord["expires"].timestamp() - time.time()
        timerthread = threading.Timer(delaySeconds, self.interpreter.expire, [actuatorUUID])
        timerthread.start()
        with self.lock:
            self.threads.append(timerthread)

    def intervalRefresh(self):
        self.interpreter.publish()
        if not self.stopped:
            self.refreshTarget += self.refreshInterval
            delaySeconds = self.refreshTarget - time.time()
            timerthread = threading.Timer(delaySeconds, self.intervalRefresh)
            timerthread.start()
            with self.lock:
                self.threads.append(timerthread)
