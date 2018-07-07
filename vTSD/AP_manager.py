import socket
import threading
import datetime
import sys, os
import json, struct
import logging

sys.path.append(os.path.abspath(os.path.join("..")))
from common.Def import MSG_HDR_LEN, MSGTYPE, INTFTYPE, ERRTYPE

from optparse import OptionParser

class Listener(object):


    def __init__(self, host, port):
        ### open the request listener n specified port
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        ### set log destination
        logging.basicConfig(filename="AP_manager.log", level=logging.DEBUG)
        logging.info("Listener is started on port " + str(port))

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            logging.info("Receive connection from " + str(address))
            client.settimeout(60)
            print threading.Thread(target = self.__listen_to_client, args = (client, address)).start()
            logging.debug("Opening a threaded socket for client " + str(address))

    def __generate_device_reg_reply(self, reg): # TODO: select  channel base don the received info
        msg = {"device_id": reg[u"device_id"], "reg_result": True, "intfs":[]}
        for intf in reg[u"intfs"]:
            msg["intfs"].append({"type":intf[u"type"], "typename":intf[u"typename"], "name":intf[u"name"], "ssid": "nrg-5-0000000", "channel": 11})
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.DEV_REG_REPLY.value, len(msg), msg)
        return msg

    def __genrate_authentication_failed_message(self):
        msg = {"err_type": ERRTYPE.AUTH_FAILED.value, "err_msg": "Authentication Failed"}
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.REG_FAILED.value, len(msg), msg)
        return msg

    def __generate_unsupported_msgtype_err(self, in_msg):
        logging.warning("Received UNSUPPORTED message: "+in_msg)
        msg = {"supported_msgs": []}
        msg["supported_msgs"] = ({"msg_type": MSGTYPE.DEV_REG.value, "msg_typename": "Device Registration"}, {"msg_type": MSGTYPE.SERVICE_EXPOSURE.value, "msg_typename": "Service Exposure"})
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.UNSUPPORTED_MSGTYPE_ERROR.value, len(msg), msg)
        return msg
                 
    def __receive_msg_hdr(self, sock):
        msg_hdr = sock.recv(MSG_HDR_LEN)
        if msg_hdr and len(msg_hdr)>2:
            logging.debug("Unpacking header "+msg_hdr)
            tp, length = struct.unpack("!BH", msg_hdr) # lenght is the length of the json data
            return (MSGTYPE(tp), length, msg_hdr)
        return (None, None, msg_hdr)
                     
    def __process_dev_reg(self, sock, tp, length):
        data = sock.recv(length)
        logging.info("Received data: "+data+"\n")

        reg = json.loads(data)
        if self.__device_is_authenticated(reg[u"device_id"], reg[u"credential"]):
            msg = self.__generate_device_reg_reply(reg)
        else:
            msg = self.__genrate_authentication_failed_message()
        return msg

    def __listen_to_client(self, client, address):
        size = 1024
        while True:
            try:
                msg_tp, datalenght, hdr_str = self.__receive_msg_hdr(client)  # data[0] = msg type; data[1] = msg length
                logging.info("Received message type [{}]:{}".format(msg_tp.value if msg_tp else "UNRECOGNIZED", msg_tp))
                # FIXME: extend message discriminator
                if msg_tp == MSGTYPE.DEV_REG:
                    response = self.__process_dev_reg(client, msg_tp, datalenght)
                else:
                    in_msg = hdr_str+client.recv(size)
                    response =self.__generate_unsupported_msgtype_err(in_msg)


                client.send(response)
                logging.debug("Replying to " + str(address) + " with " + str(response))

            # raise Exception, ('Client Disconnected')
            except:
                print "AP_manager: error ",sys.exc_info()
                logging.error( "AP_manager: error " + str(sys.exc_info()))
                client.close()
                return False

    def __device_is_authenticated(self, uuid, credentials):  #FIXME : connect to vAAA_simulation service
        response = False

        while True:
            response = raw_input("Incoming registration request from {}, cred: {}. Do you want to accept it? (yes/no) ").format( uuid, credentials)
            if (response == "yes") or (response == "no"):
                break
        if response=="yes":
            return True
        else:
            return False



if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port_num", help="select on wich port to open the listener, default = 2311", metavar="<port>")
    (options, args) = parser.parse_args()

    port_num = options.port_num

    if not port_num:
        port_num = 2311

    while True:
        try:
            port_num = int(port_num)
            break
        except ValueError:
            print "AP_manager:main: Invalid port number. Abort..."
            exit(1)

    Listener('',port_num).listen()





