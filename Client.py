#! /usr/bin/env python

import socket
import sys
import time
import threading
import select
import traceback
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class Server(threading.Thread):
    def __init__(self, receive):
        threading.Thread.__init__(self)
        self.receive = receive

    def run(self):

        lis = []
        lis.append(self.receive)
        while 1:
            read, write, err = select.select(lis, [], [])

            for item in read:
                try:
                    s = item.recv(1024)

                    if s != "":
                        chunk = s
                        print(chunk.decode() + "\n>>")
                except:
                    traceback.print_exc(file=sys.stdout)
                    break


class Client(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # create rsa keys
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=512)
        self.public_key = self.key.public_key()
        self.start()

    def connect(self, host, port):
        # Send the public key to the server
        self.sock.connect((host, port))
        self.sock.send(
            self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
        print("connected ", host, port)

    def client(self, msg):
        self.sock.send(msg)
        print("sended\n", msg)
        # print "Sent\n"

    def run(self):
        print("Client started")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        host = "127.0.0.1"
        port = 5535
        self.connect(host, port)

        user_name = input("Enter the User Name to be Used\n>>")
        receive = self.sock
        time.sleep(1)

        srv = Server(receive)
        srv.daemon = True
        srv.start()

        while 1:
            # print "Waiting for message\n"
            msg = input(">>")
            if msg == "exit":
                break
            if msg == "":
                continue
            # print "Sending\n"
            msg = user_name + ": " + msg
            data = msg.encode()
            self.client(data)
        return 1


if __name__ == "__main__":
    print("Starting client")
    cli = Client()
