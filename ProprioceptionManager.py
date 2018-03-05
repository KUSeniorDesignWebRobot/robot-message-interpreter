import uuid
import serial
import threading
import time

from ServoMessageManager import ServoMessageManager


class ProprioceptionManger:

    def __init__(self, actuators, interval):
        self.actuators = actuators
        self.lock = threading.Lock()
        self.stopped = False
        self.target = time.time()
        self.interval = interval
        self.threads = []
        t = threading.Thread(target=self.__query)
        self.threads.append(t)
        t.start()
    
    def stop(self):
        self.stopped = True
        self.joinThreads(block=True, timeout=None)

    def joinThreads(self, block=False, timeout=0):
        # try to acquire lock, just skips if block is False
        if self.lock.acquire(blocking=block):
            threads = list(self.threads)
            self.lock.release()
        else:
            return

        for thread in threads:
            if thread == threading.current_thread():
                continue
            thread.join(timeout=timeout)
            if not thread.is_alive():
                self.threads.remove(thread)

    def __query(self):
        pass
        # TODO: call something in Actuator.py to get the value, probably returns a promise like object