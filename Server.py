#! /usr/bin/env python

import socket
import sys
import traceback
import threading
import select
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

SOCKET_LIST = []
TO_BE_SENT = []
SENT_BY = {}

PUBLIC_KEYS_LIST = []

PRIVATE_SERVER_KEY_STRING = """
-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgGlFdpZB0j8ntjGvUfiUqa2jsS7dBR89JKWtNqmxSco/s6W0Vnx9
Y+qXXtenVCJUoT7pkdiiqcHg6u01/z9iMpuvKay8BsO42WEMWbg2fd5QFecxgTht
25WHo5CqP5J1fednxvH69mv+NxFAvhzKnlIonPVCMSkrEKH8N4xg+4wVAgMBAAEC
gYBicqTBRlMB3viDJItLJnQ8P85OnkHRAhRIoGFzdqoka0htGeaby4Pqep8mnISR
CoY1WKedahnJh7cMGahYNVRPjL0txz+FZ6CIQ2f/ww3M2ZtJ4PtIBlIqXUfraR+d
VEZHjk4+b1In+rDTKupLET4XUQIwHUzJUQyWnJeePPdyjQJBAMjqJmpdrGaT65cH
FUFGKyruDdPbLRCKUqauiYTqglVRPv2Yn3LUM2PocXczSKLJorzRCpDeDqxw3T24
KotHEssCQQCGIkaQj0dzmFvd0fg5vfJgxb5SvwOZ7IX3fZGmBxLXVaWVpIwgCKC2
o9v3JfbY0bz4e1wk+/p8y4TmIr4hSKCfAkALuR3ktvKISblFZrRmyqFaL+m+ottO
S8Pm1ehQSR6xu7vhMDadjKQzAC0et29VkE5elhP3v/07Mpq2LzjMR6lhAkBbw2kp
DoxgPZRjnXjG7/a4U6/P5hOtow1HcmVJAz/Vhydfx5GBfMWODW23mAZW8K3qBGLW
fngwFf+WfaA7HvebAkEApsV/4e1/Xm/IZDfbcpyEl2FLuGiJhmWEsD4gScd4DZxs
wk6dFjFOlWTi6XCR0JYfoRIWM7OULa8jJqpOGR5Phw==
-----END RSA PRIVATE KEY-----
"""


PRIVATE_SERVER_KEY = serialization.load_pem_private_key(
    data=PRIVATE_SERVER_KEY_STRING.encode(), password=None, backend=default_backend()
)


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.bind(("", 5535))
        self.sock.listen(2)
        SOCKET_LIST.append(self.sock)
        print("Server started on port 5535")

    def decrypt_message(self, message):
        return PRIVATE_SERVER_KEY.decrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        ).decode()

    def run(self):
        while 1:
            read, write, err = select.select(SOCKET_LIST, [], [], 0)

            for sock in read:
                if sock == self.sock:
                    sockfd, addr = self.sock.accept()
                    print("--- New connection from %s ---" % str(addr))

                    SOCKET_LIST.append(sockfd)
                    print("peer socket", SOCKET_LIST[len(SOCKET_LIST) - 1])

                else:
                    try:
                        message = sock.recv(1024)
                        if message == "":
                            print(str(sock.getpeername()))
                            continue
                        else:
                            try:
                                if "-----BEGIN PUBLIC KEY-----" in message.decode():
                                    PUBLIC_KEYS_LIST.append(message)
                                    print("--- Public Key Received ---")
                            except:
                                message = self.decrypt_message(message)
                                TO_BE_SENT.append(message)
                                SENT_BY[message] = str(sock.getpeername())
                    except:
                        print(str(sock.getpeername()))


class handle_connections(threading.Thread):
    def encode_message(self, message: str, public_key: bytes):
        peer_pub_key = RSA.importKey(public_key)
        encryptor = PKCS1_OAEP.new(peer_pub_key)
        return encryptor.encrypt(message.encode())

    def run(self):
        while 1:
            read, sockets_arr, err = select.select([], SOCKET_LIST, [], 0)

            for message in TO_BE_SENT:

                for idx, socket in enumerate(sockets_arr):

                    try:
                        if str(socket.getpeername()) == SENT_BY[message]:
                            print("Ignoring %s" % (str(socket.getpeername())))
                            continue

                        print("Sending to %s" % (str(socket.getpeername())))
                        encoded_message = self.encode_message(
                            message, PUBLIC_KEYS_LIST[idx]
                        )
                        print(encoded_message)
                        socket.send(encoded_message)

                    except:
                        traceback.print_exc(file=sys.stdout)
                TO_BE_SENT.remove(message)
                del SENT_BY[message]


if __name__ == "__main__":
    srv = Server()
    srv.start()
    print("Socket list", SOCKET_LIST)

    handle = handle_connections()
    handle.start()
