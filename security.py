"""
Encryption and authentication for ZMQ messages - robot side
"""

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

class Security:
    def __init__(self):
        self.baseDir = os.path.dirname(__file__)
        self.cert_dir = os.path.join(self.baseDir, 'certs')
        self.public_key_dir = os.path.join(self.baseDir, 'public_keys')
        self.secret_key_dir = os.path.join(self.baseDir, 'private_keys')
        self.serverPublicFile = ""
        self.serverPrivateFile = ""
        self.clientPublicFile = ""
        self.clientPrivateFile = ""
        self.actuatorList = [
                                {
                                    "_id": "067c8c59-710a-4c15-8265-b7f1e49b828c",
                                    "valueRange": {
                                        "gte": 0,
                                        "lt": 100
                                    },
                                    "expirationBehavior": "static",
                                    "defaultValue": 0
                                },
                                {
                                    "_id": "e1b97e17-9cd3-4361-9df3-04db98d0c829",
                                    "valueRange": {
                                        "gte": 0,
                                        "lt": 360
                                    },
                                    "expirationBehavior": "dynamic",
                                    "defaultValue": 180
                                }
                            ]
        self.actuators = [MockActuator(**a) for a in self.actuatorList]
        self.interpreter = Interpreter(self.actuators)

    def generate_cert(self, ):
        """
        Code taken from https://github.com/zeromq/pyzmq/blob/master/examples/security/generate_certificates.py
        """

        # Creating directories and removing old content
        for d in [self.cert_dir, self.public_key_dir, self.secret_key_dir]:
            if os.path.exists(d):
                shutil.rmtree(d)
            os.mkdir(d)

        # create new keys in certificates dir
        self.serverPublicFile, self.serverPrivateFile = zmq.auth.create_certificates(self.cert_dir, "server")
        self.clientPublicFile, self.clientPrivateFile = zmq.auth.create_certificates(self.cert_dir, "client")

        # move public keys to appropriate directory
        for key_file in os.listdir(self.cert_dir):
            if key_file.endswith(".key"):
                shutil.move(os.path.join(self.cert_dir, key_file),
                            os.path.join(self.public_key_dir, '.'))

        # move secret keys to appropriate directory
        for key_file in os.listdir(self.cert_dir):
            if key_file.endswith(".key_secret"):
                shutil.move(os.path.join(self.cert_dir, key_file),
                            os.path.join(self.secret_key_dir, '.'))

    def run(self):
        """
        Code taken from https://github.com/zeromq/pyzmq/blob/master/examples/security/generate_certificates.py
        """
        context = zmq.Context.instance()
        # starting authenticator for this context
        auth = ThreadAuthenticator(context)
        print("here -1")
        auth.start()
        # telling the authenticator to use certs in the directory
        auth.configure_curve(domain='*', location=self.public_key_dir)

        client_secret_file = os.path.join(self.secret_key_dir, "client.key_secret")
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
        server_public_file = os.path.join(self.public_key_dir, "server.key")
        server_public, _ = zmq.auth.load_certificate(server_public_file)
        print("here 1")
        client = context.socket(zmq.REQ)
        print("here 2")
        client.curve_secretkey = client_secret
        client.curve_publickey = client_public
        client.curve_serverkey = server_public
        print("here 5")
        client.connect(config.SERVER_ENDPOINT)

        poll = zmq.Poller()
        poll.register(client, zmq.POLLIN)

        sequence = 0
        retries_left = config.REQUEST_RETRIES
        while retries_left:
            try:
                sequence += 1
                ######### EXAMPLE VALUES ########
                request = {"message_id": "AE6893B6FA78", "message_type": "report",
                           "robot_id": "10385E45745C", "configuration_id": "1212FE080B15",
                           "session_id": "77AA0D3AE0C7", "timestamp": "23423.023423",
                           "reports": [{"sensor_id": "D9A84DFFA7CF", "ttl": 1000, "value": 1200030},
                                       {"sensor_id": "B0E2A6D4A688", "ttl": 2000, "value": 3.14159}]}
                # client.send(json.dumps(request))
                print("GOT HERE - TRY")
                client.send_json(request)
                expect_reply = True
                while expect_reply:
                    socks = dict(poll.poll(config.REQUEST_TIMEOUT))
                    if socks.get(client) == zmq.POLLIN:

                         # = client.recv_json() # if this does not work, we can do reply = json.loads(reply) in try:
                        commandMessage = 0
                        reply = 0
                        try:
                            commandMessage = CM.CommandMessage(client.recv_json())
                            reply = commandMessage.json()
                        except:
                            print("FAILED")
                        if not reply:
                            print("NO REPLY")
                            break
                        print("I: Server replied with message (%s)" % reply)
                        logging.debug("I: Server replied with message (%s)" % reply)
                        parsed_dict = {"message_id": reply["message_id"], "message_type": reply["message_type"],
                                       "robot_id": reply["robot_id"], "configuration_id": reply["configuration_id"],
                                       "session_id": reply["session_id"], "timestamp": reply["timestamp"],
                                       "instructions": list()}
                        for i in reply["instructions"]:
                            parsed_dict["instructions"].append(i)

                        # ###### CALL INPTERPRETTER PASSING parsedDict - PLEASE CORRECT IF WRONG, don't know how its structured ######
                        self.interpreter.interpret(parsed_dict)

                        retries_left = config.REQUEST_RETRIES
                        expect_reply = False

                    else:
                        logging.info("W: No response from server, retrying…")
                        # Socket is confused. Close and remove it. - PAUL'S COMMENT
                        client.setsockopt(zmq.LINGER, 0)
                        client.close()
                        poll.unregister(client)
                        retries_left -= 1
                        if retries_left == 0:
                            logging.error("E: Server seems to be offline, abandoning")
                            break
                        logging.info("I: Reconnecting and resending (%s)" % request)
                        # Create new connection
                        client = context.socket(zmq.REQ)
                        client.connect(config.SERVER_ENDPOINT)
                        poll.register(client, zmq.POLLIN)
                        print("GOT HERE - ELSE")
                        client.send_json(request)
            except KeyboardInterrupt:
                logging.info("END")
                break

        # stop auth thread
        auth.stop()
        client.close()
        context.term()
