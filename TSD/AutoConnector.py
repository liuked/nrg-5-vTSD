#!/usr/bin/env python
#-*- coding:utf-8 -*-

import commands as cmds
import os
import sys
import logging
sys.path.append(os.path.abspath(os.path.join("..")))

from common.Def import NRG5_SSID_PREFIX

class AutoConnector(object):

    def has_connectivity(self):
        pass

    def try_to_connect(self):
        pass


class WiFiAutoConnector(AutoConnector):

    def __init__(self, *args, **kwargs):
        self.password = "upmc75005"
        self.interface = None
        if "password" in kwargs:
            self.password = kwargs["password"]

    def has_connectivity(self):
        
        #tricks, non-match grep will return 1, use tee to avoid
        sh_ret, gw = cmds.getstatusoutput("ip route | grep default | tee")
        assert sh_ret==0

        return gw != ""

    def __select_intf(self, intf_list):
        """
        Description: wlan without AP support will be selected in priority
        """
        for intf in intf_list:
            sh_ret, phy = cmds.getstatusoutput("iw %s info | grep wiphy | awk '{print $2}'" % intf)
            assert sh_ret==0
            sh_ret, ap_support = cmds.getstatusoutput("iw phy{} info | grep '\* AP$' | tee".format(phy))
            assert sh_ret==0
            if ap_support == "":
                return intf
        return intf_list[0]

    def disconnect(self):
        if self.interface:
            assert os.system("ifdown {}".format(self.interface))

    def try_to_connect(self):

        sh_ret, intf_list = cmds.getstatusoutput("ip address | grep wlan | grep -v UP | gawk --re-interval '{match($0,/[^ ]*wlan[0-9]+/,a) ;print a[0]}'")
        assert sh_ret==0
        
        if intf_list == "":
            #no avaliable interfaces
            return False

        intf_list = intf_list.split("\n")
        intf = self.__select_intf(intf_list)

        sh_ret, ssid_list = cmds.getstatusoutput('ifconfig {} up && iw dev {} scan | grep "SSID:" | grep "{}" | awk {} && ifconfig {} down'.format(intf, intf, NRG5_SSID_PREFIX, "'{print $2}'", intf))
        assert sh_ret==0

        ssid = None
        if ssid_list:
            ssid = ssid_list.split("\n")[0]
        
        if ssid:
            #generate interface config in /etc/network/interface.d/<intf-name>
            with open("/etc/network/interfaces.d/{}".format(intf), "w") as f:
                f.write("iface {} inet dhcp\n".format(intf))
                f.write("    wpa-conf /etc/nrg-5/wpa/{}.conf\n".format(intf))

            #generate wpa_supplicant config in /etc/nrg-5/wpa/<intf-name>.conf
            assert os.system("mkdir -p /etc/nrg-5/wpa")==0
            with open("/etc/nrg-5/wpa/{}.conf".format(intf), "w") as f:
                f.write("country=FR\n")
                f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
                f.write("update_config=1\n")
                f.write("network={\n")
                f.write("    ssid=\"{}\"\n".format(ssid))
                f.write("    proto=RSN\n")
                f.write("    key_mgmt=WPA-PSK\n")
                f.write("    pairwise=CCMP TKIP\n")
                f.write("    group=CCMP TKIP\n")
                f.write("    psk=\"{}\"\n".format(self.password))
                f.write("}\n")
            
            #bring up the interface
            assert os.system("ifup {}".format(intf))==0

            self.interface = intf
            logging.info("connect to {} via {}".format(ssid, intf))

        return ssid != None

if __name__ == "__main__":
    connector = WiFiAutoConnector()
    print connector.has_connectivity()
    print connector.try_to_connect()
