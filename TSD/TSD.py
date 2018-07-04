#!/usr/bin/env python
#-*- coding:utf-8 -*-

import commands as cmds
import sys
import re
import os

class IntfOps(object):

	def scan(self, *args, **kwargs):
		pass

	def open(self, *args, **kwargs):
		pass
	
	def close(self, *args, **kwargs):
		pass

class WiFiIntfOps(IntfOps):

	def scan(self, *args, **kwargs):
		"""
		Description: select one spare WiFi interface, and 
		Return: (intf_name, nrg5_ap_info_list, radio_resource_usages) or None
		"""
		sh_ret, intf_list = cmds.getstatusoutput("ifconfig -a | grep wlan | grep -v UP | awk -F: '{print $1}'")
		assert sh_ret==0
		intf_list = intf_list.split("\n")
		if len(intf_list) == 0:
			return None
		
		intf = intf_list[0]
		sh_ret, bss_list = cmds.getstatusoutput('ifconfig {} up && iw dev {} scan | egrep -i "(^BSS)|(DS Parameter set: channel)|(signal:)|(SSID:)" && ifconfig {} down'.format(intf, intf, intf))
		assert sh_ret==0

		bss_list_str = bss_list.split("\n")
		bss_list = []

		for bss_index in range(0, len(bss_list_str), 4):
			bss_mac = re.match(r"BSS\s*([a-zA-Z0-9:]+).*", bss_list_str[bss_index]).group(1)
			bss_ss = re.match(r"\s*signal:\s*([-0-9\.]*\s*dBm)\s*", bss_list_str[bss_index+1]).group(1)
			bss_ssid = re.match(r"\s*SSID:\s*(\S*)\s*", bss_list_str[bss_index+2]).group(1)
			bss_chl = re.match(r"\D*(\d*)\s*", bss_list_str[bss_index+3]).group(1)
			bss_chl = int(bss_chl)
			bss_list.append({"mac":bss_mac, "signal":bss_ss, "ssid": bss_ssid, "channel":bss_chl})

		channel_usage = {}
		nrg5_bss_list = filter(lambda e:"nrg-5" in e["ssid"], bss_list)
		for bss in bss_list:
			channel = bss["channel"]
			if channel in channel_usage:
				channel_usage[channel] += 1
			else:
				channel_usage[channel] = 0

		return intf, nrg5_bss_list, channel_usage

	def open(self, *args, **kwargs):
		"""
		Description: open an wifi hotspot on a given interface, ssid and channel.
		Parameters: kwargs should include "interface" "ssid" "channel" at least
		Return: nothing
		"""
		if "interface" not in kwargs:
			raise Exception, "Open wifi hotspot without Interface"
		if "ssid" not in kwargs:
			raise Exception, "Open wifi hotspot without SSID"
		if "channel" not in kwargs:
			raise Exception, "Open wifi hotspot withou Channel"
		interface = kwargs["interface"]
		ssid = kwargs["ssid"]
		channel = kwargs["channel"]
		password = "upmc75005"
		if "password" in kwargs:
			password = kwargs["password"]
		#use the gateway as the default dns
		sh_ret, dns_server = cmds.getstatusoutput("ip route | grep default | gawk --re-interval '{match($0,/([0-9]{1,3}\.){3}[0-9]{1,3}/,a) ;print a[0]}'") 
		assert sh_ret==0
		if "dns" in kwargs:
			dns_server = kwargs["dns"]
		
		#interface, connected to upstream node/gateway
		sh_ret, gw_intf = cmds.getstatusoutput("ip route | grep default | awk -F\"dev \" '{print $2}' | awk '{print $1}'")
		assert sh_ret==0

		#stop hotspot related services
		sh_ret = os.system("service hostapd stop && service dnsmasq stop")
		assert sh_ret==0

		#rewrite the interface confiuration file, /etc/network/interfaces.d/<intfname>
		with open("/etc/network/interfaces.d/{}".format(interface), "w") as f:
			f.write("iface {} inet static\n".format(interface))
			f.write("    address 10.0.0.254\n")
			f.write("    netmask 255.255.255.0\n")

		#bring up interface
		sh_ret = os.system("ifup {}".format(interface))
		assert sh_ret==0

		#rewrite the hostapd configuration file, /etc/hostapd/hostapd.conf
		with open("/etc/hostapd/hostapd.conf", "w") as f:
			f.write("""interface={}
					ssid={}
					hw_mode=g
					channel={}
					ieee80211n=1
					ieee80211d=1
					country_code=FR
					wmm_enabled=1
					auth_algs=1
					wpa=2
					wpa_passphrase={}
					wpa_key_mgmt=WPA-PSK
					rsn_pairwise=CCMP""".format(interface, ssid, channel, password).replace(" ","").replace("\t", ""))

		#rewrite the dnsmasq configuration file, /etc/dnsmasq.conf
		with open("/etc/dnsmasq.conf", "w") as f:
			f.write("""interface={}
					listen-address=10.0.0.254
					bind-interfaces
					server={}
					domain-needed
					bogus-priv
					dhcp-range=10.0.0.1,10.0.0.253,255.255.255.0,24h""".format(interface, dns_server).replace(" ", "").replace("\t", ""))

		#enable ip forwarding 
		sh_ret = os.system("sysctl -w net.ipv4.conf.all.forwarding=1")
		assert sh_ret==0

		#add MASQUERADE NAT rules to iptable
		sh_ret = os.system("iptables -A INPUT -i {} -j ACCEPT".format(interface))
		assert sh_ret==0
		sh_ret = os.system("iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o {} -j MASQUERADE".format(gw_intf))

		#restart hostapd & dnsmasq
		sh_ret = os.system("service hostapd start && service dnsmasq start")
		assert sh_ret==0

	def close(self, *args, **kwargs):
		"""
		Description: close hotspot on specific interface
		Parameters: kwargs should contain "interface" at least
		Return: nothing
		"""
		if "interface" not in kwargs:
			raise Exception, "Close wifi hotspot without Interface"
		interface = kwargs["interface"]

		#shutdown interface
		assert os.system("ifdown {}".format(interface))==0

		#stop service
		assert os.system("service hostapd stop && service dnsmasq stop")==0

		#delete configuration file, hostapd, dnsmasq, interfaces.d/intf
		assert os.system("mv /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.lastTSD")==0
		assert os.system("mv /etc/dnsmasq.conf /etc/dnsmasq.conf.lastTSD")==0
		assert os.system("rm -f /etc/network/interfaces.d/{}".format(interface))==0
	
		#delete NAT
		assert os.system("iptables -F && iptables -t nat -F")==0


class TSD(object):

	def __init__(self, *args, **kwargs):
		pass

	def register_intf_module(self, intf_type):
		pass

	def __check_avail_intfs(self):
		pass


#testing code
if __name__ == "__main__":
	wifi_ops = WiFiIntfOps()
	print wifi_ops.scan()
	#wifi_ops.open(interface="wlan0", ssid="nrg-5-000000", channel="11")
	wifi_ops.close(interface="wlan0")
