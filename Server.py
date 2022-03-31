#! /usr/bin/env python

import socket
import sys
import traceback
import threading
import select
from cryptography.hazmat.primitives.asymmetric import dh

SOCKET_LIST = []
TO_BE_SENT = []
SENT_BY = {}

PUBLIC_KEYS_LIST = []


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
                        s = sock.recv(1024)
                        if s == "":
                            print(str(sock.getpeername()))
                            continue
                        else:
                            TO_BE_SENT.append(s)
                            SENT_BY[s] = str(sock.getpeername())
                    except:
                        print(str(sock.getpeername()))


class handle_connections(threading.Thread):
    def run(self):
        while 1:
            read, sockets_arr, err = select.select([], SOCKET_LIST, [], 0)

            for message in TO_BE_SENT:
                if "-----BEGIN PUBLIC KEY-----" in message.decode():
                    PUBLIC_KEYS_LIST.append(message)
                    print("--- Public Key Received ---")
                    print(message)
                    print("--- Public Key Received ---")

                for socket in sockets_arr:
                    try:
                        if str(socket.getpeername()) == SENT_BY[message]:
                            print(len(PUBLIC_KEYS_LIST))
                            print(len(SOCKET_LIST[1:]))

                            print("Ignoring %s" % (str(socket.getpeername())))
                            continue
                        print("Sending to %s" % (str(socket.getpeername())))
                        socket.send(message)
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
