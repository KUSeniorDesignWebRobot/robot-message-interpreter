# import security
import os
# import shutil
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
import json
import logging
import sys
import config
# from MockActuator import MockActuator
# from Interpreter import Interpreter
import CommandMessage as CM
import AcknowledgementMessage as AM
# import ReportMessageGenerator as RMG
import time
import threading
import uuid
from RepeatingTimer import RepeatingTimer

# block prints during runtime?
block = False

# Disable


def blockPrint():
    sys.stdout = open(os.devnull, 'w')


# Restore
def enablePrint():
    sys.stdout = sys.__stdout__


# Example Termination Message
tM = {
      "message_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
      "message_type": "termination",
      "timestamp": 1509748526.3482552
}


class OfflineServerError(Exception):
    pass

# lastMessageReceivedTimestamp = time.time()

class Messenger:
    def __init__(self, recv_message_type, send_message_type, manifest):
        self.recv_message_type = recv_message_type
        self.send_message_type = send_message_type
        self.context = None
        self.auth = None
        self.client = None
        self.server_side_termination = False
        self.connected = False
        # self.lastMessageReceivedTimestamp = 0
        self.manifest = manifest
        self.aliveTimer = RepeatingTimer(2.0, self.checkAlive)

    def __enter__(self):
        self.context = zmq.Context.instance()
        self.auth = ThreadAuthenticator(self.context)
        self.auth.start()
        # telling the authenticator to use the robots domain; we will randomly generate the keypair
        self.auth.configure_curve(domain='robots', location=zmq.auth.CURVE_ALLOW_ANY)
        client_public, client_secret = zmq.curve_keypair()
        server_public = (config.SERVER_PUBLIC_KEY).encode()
        self.client = self.context.socket(zmq.DEALER)
        self.client.curve_secretkey = client_secret
        self.client.curve_publickey = client_public
        self.client.curve_serverkey = server_public
        self.client.setsockopt(zmq.LINGER, 100)
        id = str.encode(self.manifest['robot_id'])
        self.client.setsockopt(zmq.IDENTITY, id)
        self.lastTime = time.time();

        self.client.connect(config.SERVER_ENDPOINT)

        self.poll = zmq.Poller()
        self.poll.register(self.client, zmq.POLLIN | zmq.POLLOUT)
        if(block):
            blockPrint()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.cleanup();

    def cleanup(self):
        self.connected = False
        enablePrint()
        if(not self.client.closed and self.is_current(2)):
            self.client.recv_json(zmq.NOBLOCK)
        if(not self.client.closed and self.is_ready_to_send(2)):
            pass
        self.auth.stop()
        while(not self.client.closed):
            self.client.disconnect(config.SERVER_ENDPOINT)
            self.client.close()
        self.context.destroy(linger=1)
        self.aliveTimer.cancel()
        try:
            self.aliveTimer.join()
        except:
            pass
        print("Finished Cleanup")

    def send(self, message):
        print("MESSAGE TYPE IS ", message["message_type"])
        print("Message being sent: \n", message)
        if(message["message_type"] == "termination"):
            self.client.send_json(message, zmq.NOBLOCK)
            print("Termination Message Sent")
        elif(self.send_message_type == "command"):
            self.client.send_json(CM.CommandMessage(message).json(), zmq.NOBLOCK)
            print("Command Message Sent")
        elif(self.send_message_type == "report"):
            self.client.send_json(message, zmq.NOBLOCK)
            print("Report Message Sent")
        elif(self.send_message_type == "acknowledgement"):
            self.client.send_json(AM.AcknowledgementMessage(message).json(), zmq.NOBLOCK)
            print("Acknowledgement Message Sent")

    def recv(self):
        message = 0
        reply = None
        received_message = None
        try:
            received_message = self.client.recv_json(zmq.NOBLOCK)
            self.lastTime = time.time();
            # self.state.updateLast(self.manifest['robot_id'], time.time())
            # print(str(self.state.instance))
            reply = received_message
        except zmq.ZMQError:
            received_message = None
        except KeyboardInterrupt:
            received_message = None
        if(received_message != None):
            if(received_message["message_type"] == "termination"):
                message = tM
                self.server_side_termination = True
                print("Received Message: \n", reply)
            elif(received_message["message_type"] == "handshake"):
                print("Received Message: \n", reply)
                pass
            elif(received_message["message_type"] == "alive"):
                self.send_alive_reply(received_message)
            elif(received_message["message_type"] == "command"):
                message = CM.CommandMessage(received_message)
                reply = message.json()
                print("Received Message: \n", reply)
            elif(received_message["message_type"] == "acknowledgement"):
                message = AM.AcknowledgementMessage(received_message)
                reply = message.json()
                print("Received Message: \n", reply)
        return reply

    def send_handshake(self):
        handshake = {
                      "message_id": str(uuid.uuid4()),
                      "message_type": "handshake",
                      "robot_id": self.manifest['robot_id'],
                      "timestamp": time.time(),
                      "manifest": self.manifest
        }
        print("Handshake message: ")
        print(handshake)
        self.client.send_json(handshake, zmq.NOBLOCK)
        # received_response = False
        print("Waiting on handshake.")
        attempt = config.REQUEST_RETRIES
        while attempt != 0:
            attempt -= 1
            try:
                reply = self.client.recv(zmq.NOBLOCK)
                print("Got handshake: ", json.loads(reply))
                self.connected = True
                self.aliveTimer.start()
                break
            except zmq.ZMQError:
                pass
            except KeyboardInterrupt:
                break
        if(not self.connected):
            print("Error: Didn't receive handshake.  Failed to connect to server after ", str(config.REQUEST_RETRIES), " attempts.")
            self.cleanup();
        return self.connected

    def send_alive_reply(self, received_message):
        aliveMessage = {
              "message_id": received_message['message_id'],
              "message_type": "alive",
              "robot_id": self.manifest['robot_id'],
              "timestamp": time.time()
        }
        self.client.send_json(aliveMessage, zmq.NOBLOCK)

    def checkAlive(self):
        timeNow = time.time()
        timeout = config.ALIVENESS_TIMEOUT
        lastTime = self.lastTime
        if timeNow - lastTime > timeout:
            print("Error: connection timeout.")
            self.cleanup();

    def is_current(self, timeout=config.REQUEST_TIMEOUT):
        socks = dict(self.poll.poll(timeout))
        status = socks.get(self.client) == zmq.POLLIN
        return status

    def is_ready_to_send(self, timeout=config.REQUEST_TIMEOUT):
        socks = dict(self.poll.poll(timeout))
        status = socks.get(self.client) == zmq.POLLOUT
        return status

    def isConnected(self):
        return self.connected
