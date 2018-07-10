#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys, os
sys.path.append(os.path.abspath(os.path.join("..")))

import time
import commands as cmds
import logging
import json
import socket
import struct
import threading
from common.Def import INTFTYPE, MSG_HDR_LEN, MSGTYPE
from common.Service import Service
from IntfOpsDef import WiFiIntfOps, IntfOps
from bitarray import bitarray


class TSD(object):

    class DNATPortPool(object):

        def __init__(self, used_ports = []):
            # do NOT use 0-1023
            self.curr_port = 0
            self.port_used = bitarray(65536 - 1024)
            self.port_used.setall(0)
            for port in used_ports:
                port -= 1024
                self.port_used[port] = 1
            self.lock = threading.Lock()

        def get_port(self):
            self.lock.acquire()

            port_start = self.curr_port
            while self.port_used[self.curr_port]:
                self.curr_port = (self.curr_port + 1) % (65536 - 1024)
                if self.curr_port == port_start:
                    raise Exception, "No free ports can be used for DNAT"

            self.port_used[self.curr_port] = 1
            port_ret = self.curr_port
            self.curr_port = (self.curr_port + 1) % (65536 - 1024)
            self.lock.release()

            return port_ret + 1024
        
        def free_port(self, port):
            port -= 1024
            self.lock.acquire()
            assert self.port_used[port]==1
            self.port_used[port] = 0
            self.lock.release()

        def reserve_port(self, port):
            port -= 1024
            self.lock.acquire()
            assert self.port_used[port]==0
            self.port_used[port]=1
            self.lock.release()


    def __init__(self, *args, **kwargs):
        """
        Description: constructor of TSD
        Parameters: kwargs may contain "intfops" which is a list storing supported interface ops object, "5Gintf" means name of 5G interface
        Return: nothing
        """
        self.active_intfs = []
        self.intf_mods = {}
        self.__load_device_info(**kwargs)
        if "intfops" in kwargs:
            for ops in kwargs["intfops"]:
                self.register_intf_module(ops)
        
        self.is_5g_gw = self.__is_5G_gateway(**kwargs)
        self.__prepare_ap_address_pool(self.is_5g_gw)
        self.__load_vTSD_info(**kwargs)
        self.dnat_port_pool = TSD.DNATPortPool()

    def __prepare_ap_address_pool(self, is_5g_gw):
        """
        Description: generate address pool
        """ 
        #FIXME: maybe we will use flexible netmask_len in the future
        self.subnet_len = 24
        if is_5g_gw:
            #10.0.0.0/24
            #10.0.1.0/24
            self.base_ap_subnet = 0xa000000
            self.current_ap_subnet = 0xa000100
            return

        #get gw ip to avoid use same subnet with gw interface
        sh_ret, gw_ip= cmds.getstatusoutput("ip route | grep default | gawk --re-interval '{match($0,/([0-9]{1,3}\.){3}[0-9]{1,3}/,a) ;print a[0]}'")
        assert sh_ret == 0

        netmask_len = self.subnet_len
        gw_ip_uint = struct.unpack("!I", socket.inet_aton(gw_ip))[0]
        netmask = (0xffffffff << (32-netmask_len)) & 0xffffffff
        
        temp = (gw_ip_uint >> (32-netmask_len)) + 1
        if temp == (0xffffffff>>(32-netmask_len)):
            temp += 2

        subnet = (temp << (32-netmask_len)) & 0xffffffff

        self.base_ap_subnet = gw_ip_uint & netmask
        self.current_ap_subnet = subnet
    
    def __assign_ap_address(self):
        """
        Return: (ip, netmask_len)
        """
        netmask_len = self.subnet_len
        subnet = self.current_ap_subnet
        
        #update self.current_ap_subnet
        self.current_ap_subnet = (self.current_ap_subnet >> (32-netmask_len)) + 1
        if self.current_ap_subnet == (0xffffffff>>(32-netmask_len)):
            self.current_ap_subnet += 2
        self.current_ap_subnet = (self.current_ap_subnet << (32-netmask_len)) & 0xffffffff

        if self.current_ap_subnet == self.base_ap_subnet:
            raise Exception, "TSD: AP address space is used up"

        ip = subnet | ((0xffffffff >> netmask_len) - 1)
        return ip, self.subnet_len


    def __is_5G_gateway(self, **kwargs):
        """
        Description: check if me is a 5G gateway
        Parameters: nothing
        Return: True or False    
        """
        # FIXME: Probably, we should change the method to judge if a device is a 5G gateway    
        # if the default route through self.intf_5g, we say that the device is a 5G gateway

        if "5Gintf" in kwargs:
            self.intf_5g = kwargs["5Gintf"]
        else:
            self.intf_5g = "eth0"
       
        sh_ret, gw_intf = cmds.getstatusoutput("ip route | grep default | awk -F\"dev \" '{print $2}' | awk '{print $1}'")
        assert sh_ret==0

        return gw_intf == self.intf_5g

    def __load_vTSD_info(self, **kwargs):
        
        # FIXME: currently, we should fixed url for vTSD, and we should setup manual dns-mapping in /etc/hosts
        vTSD_config_path = "/etc/nrg-5/vTSD.json"
        if "vTSD_config" in kwargs:
            vTSD_config_path = kwargs["vTSD_config"]

        with open(vTSD_config_path, "r") as f:
            vTSD_config = json.load(f)

        self.vTSD_url = vTSD_config[u"url"].encode("utf-8")
        self.vTSD_port = vTSD_config[u"port"]

        # remove old dns entry
        assert os.system('sed -i "/.*{}.*/d" /etc/hosts'.format(self.vTSD_url))==0

        if vTSD_config["url_resolv"] == "manual":
            #add dns mapping to /etc/hosts
            assert os.system('echo "{}    {}" >> /etc/hosts'.format(vTSD_config["ip"], self.vTSD_url))==0

        self.vTSD_ip = socket.gethostbyname(self.vTSD_url)

    def __load_device_info(self, **kwargs):
        """
        Description: load device information from a json file
        Parameters: the file is located at /etc/nrg-5/device.json unless "devinfo" is specified in kwargs
        Return: nothing
        """
        devinfo_path = "/etc/nrg-5/device.json"
        if "devinfo" in kwargs:
            devinfo_path = kwargs["devinfo"]
        
        with open(devinfo_path, "r") as f:
            devinfo = json.load(f)
            self.device_id = devinfo[u"device_id"]
            self.credential = devinfo[u"credential"]

    def register_intf_module(self, module_ops):
        assert isinstance(module_ops, IntfOps)
        assert hasattr(module_ops, "intf_type")
        intf_type = module_ops.intf_type
        assert intf_type in INTFTYPE
        if intf_type not in self.intf_mods:
            self.intf_mods[intf_type] = module_ops
            logging.info("Register the {} module".format(module_ops.intf_type_str))
        else:
            logging.warning("Try to register the {} module that was registered".format(module_ops.intf_type_str))

    def __connect_to_vTSD(self):
        """
        Description: connect to vTSD and return the socket
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.vTSD_ip, self.vTSD_port))
        return sock

    def __generate_device_register_msg(self):
        msg = {"device_id": self.device_id, "credential": self.credential, "intfs":[]}
        for t, v in self.intf_mods.iteritems():
            intf_name, nrg5_ap_list, radio_usage = v.scan()
            msg["intfs"].append({"type":v.intf_type.value, "typename":v.intf_type_str, "name":intf_name, "radio_usage":radio_usage})
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.DEV_REG.value, len(msg), msg)
        return msg

    def __receive_msg_hdr(self, sock):
        msg_hdr = sock.recv(MSG_HDR_LEN)
        tp, length = struct.unpack("!BH", msg_hdr)
        return MSGTYPE(tp), length

    def __process_dev_reg_success(self, sock, tp, length):
        reply = json.loads(sock.recv(length))
        assert reply[u"device_id"]==self.device_id
        #open hotspot
        for intf in reply[u"intfs"]:
            intf_type = INTFTYPE(intf[u"type"])
            intf_name = intf[u"name"].encode("utf-8")
            intf_channel = intf[u"channel"]
            intf_ssid = intf[u"ssid"].encode("utf-8")
            intf_ip, intf_netmask_len = self.__assign_ap_address()
            self.intf_mods[intf_type].open(interface=intf_name, ssid=intf_ssid, channel=intf_channel, ip=intf_ip, netmask_len=intf_netmask_len)
            self.active_intfs.append({"type":intf_type, "name":intf_name})
            logging.info("DEV_REG_SUCCESS on interface {} and SSID is {}".format(intf_name, intf_ssid))

    def __process_dev_reg_failed(self, sock, tp, length):
        reply = json.loads(sock.recv(length))
        assert reply[u"device_id"]==self.device_id
        logging.info("DEV_REG_FAILED({}): {}".format(reply["error_type"], reply["error_msg"]))

    def start_service(self, services=[]):
        
        #connect to vTSD
        sock = self.__connect_to_vTSD()
        
        #send registration request to vTSD
        msg = self.__generate_device_register_msg()
        sock.send(msg)
    
        #recv registration reply from vTSD
        tp, length = self.__receive_msg_hdr(sock)
 
        if tp == MSGTYPE.DEV_REG_SUCCESS:
            #expose services to vTSD at first
            for s in services:
                if not self.__register_service(s):
                    raise Exception, "Unable to register service {} on port {}".format(s.name, s.port)
            self.__launch_svs_reg_forwarder()
            self.__process_dev_reg_success(sock, tp, length)
            ret = True
        elif tp == MSGTYPE.DEV_REG_FAILED:
            self.__process_dev_reg_failed(sock, tp, length)
            ret = False
        else:
            raise Exception, "received unknown message type during start_service()"
         
        #close the connection to vTSD   
        sock.close()
        return ret

    def stop_service(self):
        for intf in self.active_intfs:
            self.intf_mods[intf["type"]].close(interface=intf["name"])
        self.fwd_server_stop = True
        self.fwd_server.join()

    def __forwarder_process_svs_reg(self, sock, tp, length):
        msg = json.loads(sock.recv(length))
        upstream_port = self.dnat_port_pool.get_port()

        upstream_intf_ip = None
        target_ip = None
        
        sh_ret, upstream_intf = cmds.getstatusoutput("ip route | grep default | awk -F\"dev \" '{print $2}' | awk '{print $1}'")
        assert sh_ret==0
        sh_ret, upstream_intf_ip = cmds.getstatusoutput("ifconfig %s | grep \"inet \" | gawk --re-interval '{match($0,/([0-9]{1,3}\.){3}[0-9]{1,3}/,a) ;print a[0]}'" % upstream_intf)
        assert sh_ret==0

        if self.is_5g_gw:
            target_ip = self.vTSD_ip
        else:
            sh_ret, target_ip = cmds.getstatusoutput("ip route | grep default | gawk --re-interval '{match($0,/([0-9]{1,3}\.){3}[0-9]{1,3}/,a) ;print a[0]}'")
            assert sh_ret==0

        #connect to target
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_sock.connect((target_ip, self.vTSD_port))

        msg["dnat_chain"].append("{}:{}".format(upstream_intf_ip, upstream_port))
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.SVS_REG.value, len(msg), msg)
        upstream_sock.send(msg)

        logging.info("forwarder: forward message {} to {} via interface {}".format(str(msg), target_ip, upstream_intf))
        
        #wait SVS_REG_SUCCESS or SVS_REG_FAILED
        tp, length = self.__receive_msg_hdr(upstream_sock)
        if tp == MSGTYPE.SVS_REG_SUCCESS:
            msg = json.loads(upstream_sock.recv(length))
            #install DNAT rule
            dnat_ip, dnat_port = msg["dnat_chain"][-1].split(":")
            dnat_intf = upstream_intf
            assert os.system("iptables -t nat -A PREROUTING -i {} -p {} --dport {} -j DNAT --to-destination {}".format(
                        dnat_intf, msg["service_proto"], dnat_port, msg["dnat_chain"][-2]))==0
            del msg["dnat_chain"][-1]

            logging.info("forwarder: install a DNAT rule: incoming(ip-{}, protocol-{}, port-{}, interface-{}), to({})".format(dnat_ip, 
                        msg["service_proto"], dnat_port, dnat_intf, msg["dnat_chain"][-1]))

            #forward to downstream device
            msg = json.dumps(msg)
            msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.SVS_REG_SUCCESS.value, len(msg), msg)
            sock.send(msg)

            logging.info("forwarder: forward SVS_REG_SUCCESS {} to downstream devices".format(str(msg)))

        elif tp == MSGTYPE.SVS_REG_FAILED:
            msg = json.loads(upstream_sock.recv(length))
            #release used port
            dnat_ip, dnat_port = msg["dnat_chain"][-1].split(":")
            self.dnat_port_pool.free_port(int(dnat_port))
            del msg["dnat_chain"][-1]

            #forward to downstream device
            msg = json.dumps(msg)
            msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.SVS_REG_FAILED.value, len(msg), msg)
            sock.send(msg)

            logging.info("forwarder: forward SVS_REG_FAILED {} to downstream devices".format(str(msg)))
        else:
            raise Exception, "received unknown message type from upstream device during __forwarder_process_svs_reg()"

        upstream_sock.close()

    def __forward_svs_reg(self, sock, addr):
        #recv registration reply from vTSD
        tp, length = self.__receive_msg_hdr(sock)
        if tp == MSGTYPE.SVS_REG:
            self.__forwarder_process_svs_reg(sock, tp, length)   
        else:
            raise Exception, "received unknown message type from downstream device during __forward_svs_reg()"
        sock.close()

    def __forwarder_server(self):
        self.fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #use the same port as vTSD for forwarder server
        #this port is unrelated to DNAT, because only downstream devices want to connect me
        self.fwd_sock.bind(("", self.vTSD_port))
        self.fwd_sock.listen(10)
        self.fwd_sock.settimeout(5)
        logging.info("Service forwarder running on port {}".format(self.vTSD_port))
        while not self.fwd_server_stop:
            try:
                cli_sock, addr = self.fwd_sock.accept()
                cli_sock.setblocking(1)
                logging.info("Forwarder: accept connection from {}".format(str(addr)))
                threading.Thread(target=self.__forward_svs_reg, args = (cli_sock, addr)).start()
            except socket.timeout:
                pass

    def __launch_svs_reg_forwarder(self):
        self.fwd_server = threading.Thread(target=self.__forwarder_server)
        self.fwd_server.start()
        self.fwd_server_stop = False

    def __process_svs_reg_success(self, sock, tp, length):
        reply = json.loads(sock.recv(length))
        assert reply[u"device_id"]==self.device_id
        logging.info("SVS_REG_SUCCESS!")

    def __process_svs_reg_failed(self, sock, tp, length):
        reply = json.loads(sock.recv(length))
        assert reply[u"device_id"]==self.device_id
        logging.info("SVS_REG_FAILED!")

    def __register_service(self, service):
        upstream_intf_ip = None
        target_ip = None
        
        sh_ret, upstream_intf = cmds.getstatusoutput("ip route | grep default | awk -F\"dev \" '{print $2}' | awk '{print $1}'")
        assert sh_ret==0
        sh_ret, upstream_intf_ip = cmds.getstatusoutput("ifconfig %s | grep \"inet \" | gawk --re-interval '{match($0,/([0-9]{1,3}\.){3}[0-9]{1,3}/,a) ;print a[0]}'" % upstream_intf)
        assert sh_ret==0

        if self.is_5g_gw:
            target_ip = self.vTSD_ip
        else:
            sh_ret, target_ip = cmds.getstatusoutput("ip route | grep default | gawk --re-interval '{match($0,/([0-9]{1,3}\.){3}[0-9]{1,3}/,a) ;print a[0]}'")
            assert sh_ret==0

        #connect to target
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((target_ip, self.vTSD_port))

        #send SVS_REG
        msg = {"device_id":self.device_id, "credential":self.credential, 
            "dnat_chain":["{}:{}".format(upstream_intf_ip, service.port)], 
            "service_type":service.type, "service_name":service.name, 
            "service_description":service.description, "service_proto":service.proto}
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.SVS_REG.value, len(msg), msg)
        sock.send(msg)

        #wait SVS_REG_SUCCESS or SVS_REG_FAILED
        tp, length = self.__receive_msg_hdr(sock)
        if tp == MSGTYPE.SVS_REG_SUCCESS:
            self.__process_svs_reg_success(sock, tp, length)
            self.dnat_port_pool.reserve_port(service.port)
            ret = True
        elif tp == MSGTYPE.SVS_REG_FAILED:
            self.__process_svs_reg_failed(sock, tp, length)
            ret = False
        else:
            raise Exception, "received unknown message type during register_service()"

        sock.close()

        return ret
            

#testing code
if __name__ == "__main__":
    #wifi_ops = WiFiIntfOps()
    #print wifi_ops.scan()
    #wifi_ops.open(interface="wlan0", ssid="nrg-5-000000", channel="11")
    #wifi_ops.close(interface="wlan0")

    tsd = TSD(intfops=[WiFiIntfOps()])
    while tsd.start_service() == False:
        #retry after 3s
        time.sleep(3)

    print raw_input("Enter any key to stop service")
    tsd.stop_service()
