import security
import os
import shutil
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
import json
import logging
import sys
import config
from MockActuator import MockActuator
from Interpreter import Interpreter
import CommandMessage as CM
import AcknowledgementMessage as AM
import ReportMessageGenerator as RMG

#block prints during runtime?
block = False

# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__

#Example Termination Message
tM = {
      "message_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
      "message_type": "termination",
      "timestamp": 1509748526.3482552
}

class OfflineServerError(Exception):
    pass

class Messenger:
    def __init__(self, recv_message_type, send_message_type):
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

    def __enter__(self):
        print("ENTER FUNCTION")
        self.context = zmq.Context.instance()
        self.auth = ThreadAuthenticator(self.context)
        self.auth.start()
        # telling the authenticator to use certs in the directory
        self.auth.configure_curve(domain='*', location=self.public_key_dir)
        self.client_public, self.client_secret = zmq.auth.load_certificate(self.client_secret_file)
        self.server_public, _ = zmq.auth.load_certificate(self.server_public_file)
        self.client = self.context.socket(zmq.REQ)
        self.client.curve_secretkey = self.client_secret
        self.client.curve_publickey = self.client_public
        self.client.curve_serverkey = self.server_public
        self.client.setsockopt(zmq.LINGER, 100)
        self.client.connect(config.SERVER_ENDPOINT)

        self.poll = zmq.Poller()
        self.poll.register(self.client, zmq.POLLIN | zmq.POLLOUT)
        if(block):
            blockPrint()
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        print("Helloooo1")
        enablePrint()
        if(self.is_current(1)):
            print("Was current")
            self.client.recv_json()
        print("EXITING WITH")
        self.auth.stop()
        print("stop auth")
        while(not self.client.closed):
            self.client.disconnect(config.SERVER_ENDPOINT)
            self.client.close()
        print("socket closed")
        self.context.destroy(linger=1)
        print("closed client")

    def send(self, message):
        if(not self.is_ready_to_send(timeout=1)):
            print("Not ready to send")
        else:
            print("SEND START")
            print("MESSAGE TYPE IS ", message["message_type"])
            try:
                if(message["message_type"] == "termination"):
                    self.client.send_json(message, zmq.NOBLOCK)
                    print("Termination Message Sent")
                elif(self.send_message_type == "command"):
                    self.client.send_json(CM.CommandMessage(message).json(), zmq.NOBLOCK)
                    print("Command Message Sent")
                elif(self.send_message_type == "report"):
                    self.client.send_json(message, zmq.NOBLOCK)
                    print("Report Message Sent")
                    # self.client.send_json(RM.ReportMessage(message).json())
                elif(self.send_message_type == "acknowledgement"):
                    self.client.send_json(AM.AcknowledgementMessage(message).json(), zmq.NOBLOCK)
                    print("Acknowledgement Message Sent")
            except:
                print("Couldn't send yet")
            print("SEND END")

    def try_resend(self, message, retries_left):
        enablePrint()
        print("RESEND START")
        retries_left -= 1
        logging.info("W: No response from server, retrying…")
        # Socket is confused. Close and remove it. - PAUL'S COMMENT
        self.client.setsockopt(zmq.LINGER, 0)
        self.client.close()
        self.poll.unregister(self.client)
        if retries_left == 0:
            logging.error("E: Server seems to be offline, abandoning")
            # raise OfflineServerError("E: Server seems to be offline, abandoning")
        else:
            logging.info("I: Reconnecting and resending (%s)" % message)
            # Create new connection
            self.client = self.context.socket(zmq.REQ)
            self.client.setsockopt(zmq.LINGER, 100)
            self.client.connect(config.SERVER_ENDPOINT)
            self.poll.register(self.client, zmq.POLLIN | zmq.POLLOUT)
            self.send(message)
            print("RESEND END")
        if(block):
            blockPrint()
        return retries_left

    def send_termination(self):
        self.send(tM)

    def recv(self):
        print("RECEIVE START")
        message = 0
        received_message = self.client.recv_json()
        if(received_message["message_type"] == "termination"):
            message = tM
            self.server_side_termination = True
        elif(self.recv_message_type == "command"):
            message = CM.CommandMessage(received_message)
        elif(self.recv_message_type == "acknowledgement"):
            message = AM.AcknowledgementMessage(self.client.recv_json())
        reply = message.json()
        logging.debug("I: Server replied with message (%s)" % reply)
        print("RECEIVE END")
        return reply

    def is_current(self, timeout=config.REQUEST_TIMEOUT):
        print("IS_CURRENT START")
        socks = dict(self.poll.poll(timeout))
        status = socks.get(self.client) == zmq.POLLIN
        print("IS_CURRENT END")
        return status

    def is_ready_to_send(self, timeout=config.REQUEST_TIMEOUT):
        print("is_ready_to_send START")
        socks = dict(self.poll.poll(timeout))
        status = socks.get(self.client) == zmq.POLLOUT
        print("is_ready_to_send END")
        return status
