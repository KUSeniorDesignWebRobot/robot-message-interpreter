import threading
import queue
import uuid
import time
import json

from Report import Report

class ReportMessageGenerator:
    def __init__(self, interval=0.05):
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.stopped = False
        self.target = time.time()
        self.interval = interval
        self.threads = []
        t = threading.Thread(target=self.__consume)
        self.threads.append(t)
        t.start()

    def stop(self):
        self.queue.join()
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

    def __consume(self):
        reports = []
        # wait until the queue isn't empty
        while not self.queue.empty():
            reports.append(self.queue.get_nowait())
            self.queue.task_done()
        if reports:
            message = self.generateReportMessage(reports)
            self.sendReportMessage(message)
        self.joinThreads()

        if not self.stopped:
            self.target += self.interval
            delaySeconds = self.target - time.time()
            timerthread = threading.Timer(delaySeconds, self.__consume)
            timerthread.start()
            with self.lock:
                self.threads.append(timerthread)

    def generateReportMessage(self, reports):
        # TODO figure out where to get robot_id and session_id
        message = {
            "message_id": uuid.uuid4(),
            "message_type": "report",
            "robot_id": "REPLACEME",
            "session_id": "REPLACEME",
            "timestamp": time.time()
        }
        message["reports"] = [r.asDict() for r in reports]
        return message

    def sendReportMessage(self, message):
        message["message_id"] = str(message["message_id"])
        print(json.dumps(message))
        # TODO hook this up to some type of sender @paul

    def enqueue(self, report):
        """
        Adds a Report to the queue (non blocking)
        """
        t = threading.Thread(target=self.__enqueue, args=(report,))
        t.start()

    def __enqueue(self, report):
        self.queue.put(report)
        with self.lock:
            self.threads.append(threading.current_thread())
