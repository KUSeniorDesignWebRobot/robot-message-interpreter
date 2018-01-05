#  Author: Paul McELroy
#  Based off of basic code on the ZMQ guide
#  by Daniel Lundin:
##
##  Lazy Pirate client
##  Use zmq_poll to do a safe request-reply
##  To run, start lpserver and then randomly kill/restart it
##
##   Author: Daniel Lundin <dln(at)eintr(dot)org>
##
from __future__ import print_function

import os
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator

import json
import time
from pprint import PrettyPrinter

from MockActuator import MockActuator
from Interpreter import Interpreter


actuatorList = [
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

def is_json(myjson):
    answer = True
    try:
        json_object = json.loads(myjson)
    except (ValueError):
        answer = False
    return answer

REQUEST_TIMEOUT = 2500
REQUEST_RETRIES = 30
SERVER_ENDPOINT = "tcp://localhost:5555"

base_dir = os.path.dirname(__file__)
public_keys_dir = os.path.join(base_dir, 'public_keys')
secret_keys_dir = os.path.join(base_dir, 'private_keys')


context = zmq.Context(1)
auth = ThreadAuthenticator(context)
auth.start()
auth.configure_curve(domain='*', location=public_keys_dir)

client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
server_public_file = os.path.join(public_keys_dir, "server.key")
server_public, _ = zmq.auth.load_certificate(server_public_file)


print("I: Connecting to server…")
client = context.socket(zmq.REQ)
client.curve_secretkey = client_secret
client.curve_publickey = client_public
client.curve_serverkey = server_public
client.connect(SERVER_ENDPOINT)

poll = zmq.Poller()
poll.register(client, zmq.POLLIN)


sequence = 0
retries_left = REQUEST_RETRIES


pp = PrettyPrinter()
actuators = [MockActuator(**a) for a in actuatorList]
interpreter = Interpreter(actuators)


while retries_left:
    try:
        sequence += 1
        request = str("RabbitBot").encode()
        print("I: Sending (%s)" % request)
        client.send(request)

        expect_reply = True
        while expect_reply:
            print("Current state:", pp.pformat(interpreter.actuatorRecords))
            # messageStr = str(input("message: "))

            socks = dict(poll.poll(REQUEST_TIMEOUT))
            if socks.get(client) == zmq.POLLIN:
                reply = client.recv()
                if not reply:
                    break
                # if reply == request:
                if is_json(reply):
                    print("I: Server replied OK (%s)" % reply)
                    message = json.loads(messageStr)
                    if "timestamp" not in message:
                        message["timestamp"] = time.time()
                    interpreter.interpret(message)

                    retries_left = REQUEST_RETRIES
                    expect_reply = False
                else:
                    print("E: Malformed reply from server: %s" % reply)

            else:
                print("W: No response from server, retrying…")
                # Socket is confused. Close and remove it.
                client.setsockopt(zmq.LINGER, 0)
                client.close()
                poll.unregister(client)
                retries_left -= 1
                if retries_left == 0:
                    print("E: Server seems to be offline, abandoning")
                    break
                print("I: Reconnecting and resending (%s)" % request)
                # Create new connection
                client = context.socket(zmq.REQ)
                client.connect(SERVER_ENDPOINT)
                poll.register(client, zmq.POLLIN)
                client.send(request)
    except KeyboardInterrupt:
        print("END")
        retries_left = False
        break

# stop auth thread
auth.stop()
client.close()
context.term()
