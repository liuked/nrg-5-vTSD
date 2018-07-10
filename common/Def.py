#!/usr/bin/env python
#-*- coding:utf-8 -*-

from enum import Enum

NRG5_SSID_PREFIX="nrg-5-"

class INTFTYPE(Enum):
	WIFI = 1

#1B type + 2B len
MSG_HDR_LEN = 3

class MSGTYPE(Enum):
    DEV_REG = 0x01
    DEV_REG_SUCCESS = 0x02
    DEV_REG_FAILED = 0x05
    SVS_REG = 0x03
    SVS_REG_SUCCESS = 0x04
    SVS_REG_FAILED = 0x06
    UNSUPPORTED_MSG_TYPE_ERROR = 0xff
