#  Author: Paul McELroy
#  Based off of basic code on the ZMQ guide
#  by Daniel Lundin:
##  Lazy Pirate server
##  Binds REQ socket to tcp://*:5555
##  Like hwserver except:
##   - echoes request as-is
##   - randomly runs slowly, or exits to simulate a crash.
##
##   Author: Daniel Lundin <dln(at)eintr(dot)org>
##
from __future__ import print_function

from random import randint
import time
import os
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator

import json


context = zmq.Context(1)
base_dir = os.path.dirname(__file__)
public_keys_dir = os.path.join(base_dir, 'public_keys')
secret_keys_dir = os.path.join(base_dir, 'private_keys')

auth = ThreadAuthenticator(context)
auth.start()
auth.allow('127.0.0.1')
auth.configure_curve(domain='*', location=public_keys_dir)

server_secret_file = os.path.join(secret_keys_dir, "server.key_secret")
server_public, server_secret = zmq.auth.load_certificate(server_secret_file)

server = context.socket(zmq.REP)

server.curve_secretkey = server_secret
server.curve_publickey = server_public
server.curve_server = False
server.bind("tcp://*:5555")

cycles = 0
while True:
    try:
        request = server.recv()
        cycles += 1
        print("I: Normal request (%s)" % request)
        # print("Current state:", pp.pformat(interpreter.actuatorRecords))
        messageStr = str(input("message: "))
        print(type(messageStr.decode('utf-8')))
        print(messageStr.decode('utf-8'))
        if messageStr != "":
            # message = json.loads(messageStr)
            # if "timestamp" not in message:
            #     message["timestamp"] = time.time()
            # messageStr = str(message)
            # interpreter.interpret(message)
            server.send(messageStr)

    except KeyboardInterrupt:
        print("END")
        break
auth.stop()
server.close()
context.term()
