#!/usr/bin/env python
#-*- coding:utf-8 -*-

from enum import Enum

class INTFTYPE(Enum):
	WIFI = 1

#1B type + 2B len
MSG_HDR_LEN = 3

class MSGTYPE(Enum):
	DEV_REG = 0x01
	DEV_REG_REPLY = 0x02
	SERVICE_EXPOSURE = 0x03
	SERVICE_EXPOSURE_REPLY = 0x04


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
