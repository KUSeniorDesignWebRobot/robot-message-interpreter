import threading
import queue
import serial
import logging
import promise
import time

from ServoMessage import ServoMessage
from ManifestReader import ManifestReader

class ServoMessageManager(object):
    """
    Singleton manager for sending servo messages
    Must call stop() before discarding
    """

    instance = None

    class __ServoMessageManager:
        def __init__(self, interval=0.01):
            self.manifestReader = ManifestReader()
            self.testing = self.manifestReader.getVar('testing')

            self.lock = threading.Lock()
            self.queue = queue.Queue()

            if not self.testing:
                self.serial = serial.Serial('/dev/ttyUSB0')
                if self.serial is None:
                    raise IOError("Serial Connection Failed!")
                    logging.error("Serial Connection Failed!")
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
            messages = []
            # wait until the queue isn't empty
            with self.lock:
                while not self.queue.empty():
                    message = self.queue.get_nowait()
                    messages.append(message)
                    self.queue.task_done()
            if messages:
                self.sendMessages(messages)
            self.joinThreads()

            if not self.stopped:
                self.target += self.interval
                delaySeconds = self.target - time.time()
                timerthread = threading.Timer(delaySeconds, self.__consume)
                timerthread.start()
                with self.lock:
                    self.threads.append(timerthread)


        def getMessage(self):
            return ServoMessage(self)

        def sendMessages(self, messages):
            # select only last message received per channel
            sendableMessages = {}
            for message in messages:
                sendableMessages[message.channel] = message
            messages = sendableMessages.values()

            channel_messages = []
            for message in messages:
                channel_message = b"#%d P%d" % (message.channel, message.value)
                logging.info("message sent on channel %d with value %d", message.channel, message.value)
                if message.time:
                    channel_message += b" T%d" % (message.time,)
                    logging.info("message sent at time %d", message.time)
                elif message.speed:
                    channel_message += b" S%d" % (message.speed,)
                    logging.info("message speed at %d", message.speed)
                channel_messages.append(channel_message)
            serial_message = b" ".join(channel_messages) + b"\r"

            if not self.testing:
                self.serial.write(serial_message)


        def enqueue(self, message):
            """
            Adds a ServoMessage to the queue (non blocking)
            """
            t = threading.Thread(target=self.__enqueue, args = (message,))
            t.start()

        def __enqueue(self, message):
            self.queue.put(message)
            with self.lock:
                self.threads.append(threading.current_thread())

    def __new__(cls, interval=0.01):
        if not ServoMessageManager.instance:
            ServoMessageManager.instance = ServoMessageManager.__ServoMessageManager(interval)
        return ServoMessageManager.instance
