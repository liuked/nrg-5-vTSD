import socket
import threading
import datetime

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
            threading.Thread(target = self.listenToClient, args = (client, address)).start()
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
                    self.createlog("Opening a threaded socket for client " + str(dadress))
                    raise error('Client Disconnected')
            except:
                client.close()
                return False

    def createlog(self, message):
        with open('listener.log', 'a') as logfile:
            logfile.write("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "] " + str(message) + '\n')


if __name__ == "__main__":
    while True:
        port_num = raw_input("Port? ")
        try:
            port_num = int(port_num)
            break
        except ValueError:
            pass

    Listener('',port_num).listen()





