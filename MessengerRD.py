# import security
import os
# import shutil
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
# import json
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


class Messenger:
    def checkAlive(self):
        if self.lastMessageReceivedTimestamp - time.time() > config.REQUEST_TIMEOUT:
            print("Error: connection timeout.")
            self.aliveTimer.stop()
            enablePrint()
            if(self.is_current(2)):
                self.client.recv_json(zmq.NOBLOCK)
            if(self.is_ready_to_send(2)):
                pass
            self.auth.stop()
            while(not self.client.closed):
                self.client.disconnect(config.SERVER_ENDPOINT)
                self.client.close()
            self.context.destroy(linger=1)

    def __init__(self, recv_message_type, send_message_type, manifest):
        self.recv_message_type = recv_message_type
        self.send_message_type = send_message_type
        self.baseDir = os.path.dirname(__file__)
        self.cert_dir = os.path.join(self.baseDir, 'certs')
        self.public_key_dir = os.path.join(self.baseDir, 'public_keys')
        self.secret_key_dir = os.path.join(self.baseDir, 'private_keys')
        self.server_public_file = os.path.join(self.public_key_dir, "server.key")
        self.serverPrivateFile = ""
        self.clientPublicFile = ""
        self.client_secret_file = os.path.join(self.secret_key_dir, "client.key_secret")
        self.client_secret_file = os.path.join(self.secret_key_dir, "client.key_secret")
        self.client_public, self.client_secret = "", ""
        self.server_public_file = os.path.join(self.public_key_dir, "server.key")
        self.server_public = ""
        self.context = None
        self.auth = None
        self.client = None
        self.server_side_termination = False
        self.connected = False
        self.lastMessageReceivedTimestamp = 0
        self.aliveTimer = threading.Timer(config.REQUEST_TIMEOUT, self.checkAlive)
        self.manifest = manifest

    def __enter__(self):
        self.context = zmq.Context.instance()
        self.auth = ThreadAuthenticator(self.context)
        self.auth.start()
        # telling the authenticator to use certs in the directory
        self.auth.configure_curve(domain='*', location=self.public_key_dir)
        self.client_public, self.client_secret = zmq.auth.load_certificate(self.client_secret_file)
        self.server_public, _ = zmq.auth.load_certificate(self.server_public_file)
        self.client = self.context.socket(zmq.DEALER)
        self.client.curve_secretkey = self.client_secret
        self.client.curve_publickey = self.client_public
        self.client.curve_serverkey = self.server_public
        self.client.setsockopt(zmq.LINGER, 100)
        id = str.encode(self.manifest['robot_id'])
        self.client.setsockopt(zmq.IDENTITY, id)

        self.client.connect(config.SERVER_ENDPOINT)

        self.poll = zmq.Poller()
        self.poll.register(self.client, zmq.POLLIN | zmq.POLLOUT)
        if(block):
            blockPrint()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
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
        except zmq.ZMQError:
            received_message = None
        except KeyboardInterrupt:
            received_message = None
        if(received_message is not None):
            if(received_message["message_type"] == "termination"):
                message = tM
                self.server_side_termination = True
            elif(self.recv_message_type == "command"):
                message = CM.CommandMessage(received_message)
            elif(self.recv_message_type == "acknowledgement"):
                message = AM.AcknowledgementMessage(received_message)
            elif(self.recv_message_type == "handshake"):
                pass
            elif(self.recv_message_type == "alive"):
                self.client.send_alive_reply(received_message)
            reply = message.json()
            logging.debug("I: Server replied with message (%s)" % reply)
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
        while attempt is not 0:
            attempt -= 1
            try:
                self.client.recv(zmq.NOBLOCK)
                print("Got handshake.")
                self.connected = True
                self.lastMessageReceivedTimestamp = time.time()
                self.aliveTimer.start()
                break
            except zmq.ZMQError:
                pass
            except KeyboardInterrupt:
                break
        if(not self.connected):
            print("Error: Didn't receive handshake.  Failed to connect to server after ", str(config.REQUEST_RETRIES), " attempts.")
            enablePrint()
            if(self.is_current(2)):
                self.client.recv_json(zmq.NOBLOCK)
            if(self.is_ready_to_send(2)):
                pass
            self.auth.stop()
            while(not self.client.closed):
                self.client.disconnect(config.SERVER_ENDPOINT)
                self.client.close()
            self.context.destroy(linger=1)
        return self.connected

    def send_alive_reply(self, received_message):
        aliveMessage = {
              "message_id": received_message['message_id'],
              "message_type": "alive",
              "robot_id": self.manifest['robot_id'],
              "timestamp": time.time()
        }
        self.client.send_json(aliveMessage, zmq.NOBLOCK)
        print("Alive Reply Message Sent")

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
