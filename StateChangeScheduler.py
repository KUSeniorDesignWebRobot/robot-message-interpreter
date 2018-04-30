import time
import threading
import logging
import queue
from ScheduledAction import ScheduledAction

class StateChangeScheduler:
    """
    Handles scheduling of state refresh and multithreaded timing for an Interpreter
    """

    def __init__(self, interpreter, refreshInterval):
        """
        :param Interpreter interpreter: The interpreter to run state change functions on
        :param float refreshInterval: The refresh interval for state changes in seconds
        """
        self.num_workers = 8
        self.interpreter = interpreter
        self.refreshInterval = refreshInterval
        self.refreshTarget = time.time()
        self.threads = []
        self.worker_threads = []
        self.lock = threading.Lock()
        self.stopped = False
        self.intervalRefresh()
        self.queue = queue.PriorityQueue()
        for i in range(0, self.num_workers):
            thread = threading.Thread(target=self._worker)
            thread.start()
            self.worker_threads.append(thread)


    def _worker(self):
        sleep_time_sec = 0.02
        while not self.stopped:
            try:
                action = self.queue.get(timeout=1)
                self.queue.task_done()
            except queue.Empty:
                time.sleep(sleep_time_sec)
                continue
            if action[0] > time.time():
                # action not ready yet
                next_time = action[0]
                self.queue.put(action)
                time.sleep(min(next_time - time.time(), sleep_time_sec))
            else:
                action[1].run()
                time.sleep(sleep_time_sec)

    def stop(self):
        print("StateChangeScheduler.stop") #TODO deleteme
        logging.info("state change scheduler stopped")
        self.queue.join()
        print("Joined task queue")
        with self.lock:
            print("\tgot lock") #TODO deleteme
            logging.info("state change scheduler got lock")
            self.stopped = True
        # wait for all threads to rejoin
        print("\tjoining threads") #TODO deleteme
        logging.info("state change scheduler joining threads")
        self.joinThreads(block=True, timeout=None)
        print("\tjoined threads") #TODO deleteme
        for worker in self.worker_threads:
            worker.join()
        print("joined worker threads")
        logging.info("state change scheduler joined threads")

    def showThreads(self):
        print(threading.enumerate())
        logging.info("active threads %s",threading.enumerate() )

    def joinThreads(self, block=False, timeout=0):
        # try to acquire lock, just skips if block is False
        print("StateChangeScheduler.joinThreads") #TODO deleteme
        logging.info("StateChangeScheduler.joinThreads")
        if self.lock.acquire(blocking=block):
            print("\tgot lock") #TODO deleteme
            logging.info("state change scheduler got lock")
            threads = list(self.threads)
            self.lock.release()
        else:
            return
        print("\tjoining ", len(threads), " threads")
        logging.info("joining %i threads", len(threads))
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
        actionTime = command["adjusted_timestamp"]
        action = (actionTime, ScheduledAction(
            args=[command],
            kwargs={},
            function=self.interpreter.apply,
            timestamp=actionTime
        ))
        self.queue.put(action)

    def scheduleExpiration(self, actuatorUUID):
        """
        Checks for message expiration of the specified actuatorUUID and takes appropriate action
        :param uuid.UUID actuatorUUID: The UUID of the actuator to perform expiration validation on
        """
        actuatorRecord = self.interpreter.actuatorRecords[actuatorUUID]
        actionTime = actuatorRecord["expires"].timestamp()
        action = (actionTime, ScheduledAction(
            args=[actuatorUUID],
            kwargs={},
            function=self.interpreter.expire,
            timestamp=actionTime
        ))
        self.queue.put(action)

    def intervalRefresh(self):
        self.interpreter.publish()
        if not self.stopped:
            self.refreshTarget += self.refreshInterval
            delaySeconds = self.refreshTarget - time.time()
            timerthread = threading.Timer(delaySeconds, self.intervalRefresh)
            timerthread.start()
            with self.lock:
                self.threads.append(timerthread)
