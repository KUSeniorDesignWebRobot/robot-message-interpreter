#Found here: https://stackoverflow.com/questions/29769332/how-to-create-a-background-threaded-on-interval-function-call-in-python
from threading import Timer

class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)
#
#
# t = RepeatingTimer(30.0, self.mqConn.heartbeat_tick)
# t.start() # every 30 seconds, call heartbeat_tick
#
# # later
# t.cancel() # cancels execution
