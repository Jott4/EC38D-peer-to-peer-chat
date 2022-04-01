#! /usr/bin/env python

from ast import Bytes
import socket
import sys
import time
import threading
import select
import traceback
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto import Random

random_generator = Random.new().read


RSA_KEY = RSA.generate(1024, random_generator)


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
                    byte_encoded_msg = item.recv(1024)

                    if byte_encoded_msg != "":
                        decryptor = PKCS1_OAEP.new(RSA_KEY)
                        decrypted = decryptor.decrypt(byte_encoded_msg)
                        print(decrypted.decode() + "\n>>")
                except:
                    traceback.print_exc(file=sys.stdout)
                    break


class Client(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # get server public key
        with open("./public-server-key.pem", "rb") as key_file:
            self.server_public_key = serialization.load_pem_public_key(key_file.read())

        # create rsa keys
        self.key = RSA_KEY
        self.public_key = self.key.public_key()

        self.start()

    def connect(self, host, port):
        self.sock.connect((host, port))
        # Send the public key to the server
        self.sock.send(self.public_key.exportKey(format="PEM", passphrase=None, pkcs=1))
        print("connected ", host, port)

    def client(self, msg):
        cipher = self.server_public_key.encrypt(
            msg,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        self.sock.send(cipher)

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
