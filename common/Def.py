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
