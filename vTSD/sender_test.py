import socket
import sys

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
            print "Sending \""+ message+"\""
            try:
                self.sock.send(message)
                data = self.sock.recv(buffsize)
                print "Received \""+data+"\""
            except socket.error, exc:
                print "socket.error: %s" % exc
                exit(1)


if __name__ == "__main__":

    while True:
        address = str(raw_input("Address? "))
        try:
            if address.count('.') < 3:
                raise  socket.error
            #socket.inet_aton(address)
            break
        except socket.error:
            print "Not a valid IP..."
            pass

    while True:
        port_num = raw_input("Port? ")
        try:
            port_num = int(port_num)
            if port_num > 65535:
                raise ValueError
            break
        except ValueError:
            print "Invalid port number (0 < port < 65535)"
            pass

    Sender(address, port_num).console()