import security
import os
import shutil
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
import json
import logging

import config
from MockActuator import MockActuator
from Interpreter import Interpreter
import CommandMessage as CM
import AcknowledgementMessage as AM

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
        self.client.connect(config.SERVER_ENDPOINT)

        self.poll = zmq.Poller()
        self.poll.register(self.client, zmq.POLLIN)
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        print("EXITING WITH")
        self.auth.stop()
        print("stop auth")
        self.client.close()
        print("closed client")
        self.context.term()
        print("terminated context")

    def send(self,message):
        print("SEND START")
        if(self.send_message_type == "command"):
            self.client.send_json(CM.CommandMessage(message).json())
        elif(self.send_message_type == "acknowledgement"):
            self.client.send_json(AM.AcknowledgementMessage(message).json())
        print("SEND END")

    def try_resend(self, message, retries_left):
        print("RESEND START")
        retries_left -= 1
        logging.info("W: No response from server, retrying…")
        # Socket is confused. Close and remove it. - PAUL'S COMMENT
        self.client.setsockopt(zmq.LINGER, 0)
        self.client.close()
        self.poll.unregister(self.client)
        if retries_left == 0:
            logging.error("E: Server seems to be offline, abandoning")
            raise OfflineServerError("E: Server seems to be offline, abandoning")
        logging.info("I: Reconnecting and resending (%s)" % message)
        # Create new connection
        self.client = self.context.socket(zmq.REQ)
        self.client.connect(config.SERVER_ENDPOINT)
        self.poll.register(self.client, zmq.POLLIN)
        self.send(message)
        print("RESEND END")
        return retries_left


    def recv(self):
        print("RECEIVE START")
        message = 0
        if(self.recv_message_type == "command"):
            message = CM.CommandMessage(self.client.recv_json())
        elif(self.recv_message_type == "acknowledgement"):
            message = AM.AcknowledgementMessage(self.client.recv_json())
        reply = message.json()
        logging.debug("I: Server replied with message (%s)" % reply)
        print("RECEIVE END")
        return reply

    def is_current(self):
        print("IS_CURRENT START")
        socks = dict(self.poll.poll(config.REQUEST_TIMEOUT))
        status = socks.get(self.client) == zmq.POLLIN
        print("IS_CURRENT END")
        return status
