import socket
import sys, os
import json
import struct

sys.path.append(os.path.abspath(os.path.join("..")))
from common.Def import MSG_HDR_LEN, MSGTYPE, INTFTYPE, ERRTYPE

class Sender(object):

    def __init__(self, dest, port):
        self.dest = dest
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print "Connecting to ", dest , ":", port
        try:
            self.sock.connect((dest, port))
            print "Succeed! You can start typing messages... \n\n"
        except socket.error, exc:
            print "socket.error: %s" % exc
            exit(1)

    def console(self):
        buffsize = 1024
        while True:
            message = str(raw_input("Message? "))
            if message == "":
                pass
            if message == "g":
                message = self.__gen_reg_msg()
            if message == "r":
                message = self.__gen_random_msg()
            print "Sending \""+ str(message)+"\""
            try:
                self.sock.send(message)
                data = self.sock.recv(buffsize)
                print "Received \""+data+"\""
            except socket.error, exc:
                print "socket.error: %s" % exc
                exit(1)


    def __gen_reg_msg(self):
        msg = {"device_id": 0xff25ac6de4, "credential": "canedio", "intfs": []}
        msg["intfs"].append(
            {"type": 1, "typename": "WIFI", "name": "wlan0", "radio_usage": "free"})
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.DEV_REG.value, len(msg), msg)
        return msg


    def __gen_random_msg(self):
        msg = {"device_id": 0xff25ac6de4, "credential": "canedio", "intfs": []}
        msg["intfs"].append(
            {"type": 1, "typename": "WIFI", "name": "wlan0", "radio_usage": "free"})
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), 2, len(msg), msg)
        return msg


if __name__ == "__main__":

    while True:
        address = "127.0.0.1"

        # address = str(raw_input("Address? "))
        try:
            if address.count('.') < 3:
                raise  socket.error
            #socket.inet_aton(address)
            break
        except socket.error:
            print "Not a valid IP..."
            pass

    while True:
        port_num = 2311
        # port_num = raw_input("Port? ")
        try:
            port_num = int(port_num)
            if port_num > 65535:
                raise ValueError
            break
        except ValueError:
            print "Invalid port number (0 < port < 65535)"
            pass

    Sender(address, port_num).console()

