#!/usr/bin/env python
#-*- coding:utf-8 -*-

class Service(object):

    def __init__(self, tp, name, description, port, proto, *args, **kwargs):
        """
            e.g.: 1, "Web", "Web", 8080, "tcp"
        """
        self.type = tp
        self.name = name
        self.description = description
        self.port = port
        self.proto = proto
