import socket
import threading
import datetime
from optparse import OptionParser

class Listener(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.createlog("Listener is started on port " + str(port))

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            self.createlog("Receive connection from " + str(address))
            client.settimeout(60)
            print threading.Thread(target = self.listenToClient, args = (client, address)).start()
            self.createlog("Opening a threaded socket for client " + str(address))

    def listenToClient(self, client, address):
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    response = data+data
                    client.send(response)
                    self.createlog("Replying to " + str(address) + " with " + str(response))
                else:
                    raise error('Client Disconnected')
            except msg:
                print "AP_manager: error "
                client.close()
                return False

    def createlog(self, message):
        with open('listener.log', 'a') as logfile:
            logfile.write("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "] " + str(message) + '\n')


if __name__ == "__main__":

    port_num = 2311

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", help="select on wich port to open the listener, default = 2311", metavar="<port>")
    (options, args) = parser.parse_args()

    while True:
        port_num = options.port
        try:
            port_num = int(port_num)
            break
        except ValueError:
            print "AP_manager:main: Invalid port number. Abort..."
            exit(1)

    Listener('',port_num).listen()





