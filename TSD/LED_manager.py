import sys, os
sys.path.append(os.path.abspath(os.path.join("..")))

import RPi.GPIO as IO
import time
import threading
from common.Def import bcolors

class LED(object):
    SOURCE = True;  # TURNS ON IF PIN HIGH
    DRAIN = False;  # TURNS ON IF PIN LOW

    ON = 1;
    OFF = 0;
    BLINKING = 2;

    def __init__(self, pin, conf):
        # print "Creating new LED on pin {} as {}".format(pin,conf)
        self.pin = pin
        self.conf = conf
        self.status = not conf
        IO.setup(pin, IO.OUT)
        IO.output(pin, IO.LOW if conf else IO.HIGH)

    def turn_on(self, update_status=True):
        IO.output(self.pin, IO.HIGH if self.conf else IO.LOW)
        if update_status:
            # print "LED: Turning ON pin", self.pin
            self.status = LED.ON 

    def turn_off(self, update_status=True):
        IO.output(self.pin, IO.LOW if self.conf else IO.HIGH)
        if update_status:
            # print "LED: Turning OFF pin", self.pin
            self.status = LED.OFF 

    def start_blinking(self, t_on, t_off):
        if self.status == LED.BLINKING:
            # print "LED: Already blinking"
        else:
            # print "LED: Starting thread to blink pin", self.pin
            self.__stop_blnk = threading.Event()
            threading.Thread(target=self.__blink, args=(t_on, t_off, self.__stop_blnk)).start()
            self.status = LED.BLINKING


    def __blink(self, t_on, t_off, stop_event):
	# print bcolors.OKBLUE+"LED: blink thread {}: started".format(self.pin)+bcolors.ENDC
        while (not stop_event.is_set()):
            self.turn_on(False)
            stop_event.wait(t_on)
            self.turn_off(False)
            stop_event.wait(t_off)
            pass
	# print bcolors.OKBLUE+"LED: blink thread {}: stopped".format(self.pin)+bcolors.ENDC

    def stop_blinking(self):
        if self.status == LED.BLINKING:
            # print "LED: Stopping to blink pin", self.pin
            self.__stop_blnk.set()
            self.turn_off()

    def toggle(self):
        # print "LED: toggle pin", self.pin
        self.turn_off() if self.status == LED.ON else self.turn_on()


    def lamp(self, intervals):
        if self.status != LED.BLINKING:
            # print "LED: Starting thread to lamp pin", self.pin
            threading.Thread(target=self.__lamp_thread, args=(intervals)).start()
        else:
            # print bcolors.WARNING+"LED: warning - Led BLINKINg"

    def __lamp_thread(self, *intervals):
        # print "lampthread Started"
        prev_stat = self.status #seve previous status
        self.turn_off()  #first turn off, then start the sequence
        time.sleep(0.5)
        for t in intervals:
            self.toggle()
            time.sleep(t)
        # restore previous status
        self.turn_off() if prev_stat == LED.OFF else self.turn_on()
	# print "lampthread stopped"

class LedManager(object):

    def __init__(self, leds):
        # print "LedManager: Starting with ", leds
        IO.setmode(IO.BOARD)
        self.__leds = {}
        for led in leds:
            self.add_led(led[0], led[1], led[2])

    def add_led(self, ledname, pin, conf):
        assert ledname not in self.__leds
        # print "LedManager: Adding led ", ledname, "at pin", pin, "in conf", conf
        self.__leds[ledname] = LED(pin, conf)

    def led_turn_on(self, ledname):
        """
        :param ledname: name of the led in ledmanager
        :return: nothing
        """
        assert ledname in self.__leds
        if ledname in self.__leds:
            if self.__leds[ledname].status == LED.BLINKING:
                # print bcolors.FAIL+"LedManager: err - led is blinking"+bcolors.ENDC
            else:
                # print "LedManager: Turning led", ledname, "ON"
                self.__leds[ledname].turn_on()

    def led_turn_off(self, ledname):
        """
        :param ledname: name of the led in ledmanager
        :return: nothing
        """
        # print "LedManager: Turning led", ledname, "OFF"
        assert ledname in self.__leds
        if ledname in self.__leds:
            if self.__leds[ledname].status == LED.BLINKING:
                # print bcolors.WARNING+"LedManager: warning - led was blinking. stopping..."+bcolors.ENDC
                self.__leds[ledname].stop_blinking()
            self.__leds[ledname].turn_off()

    def led_start_blinking(self, ledname, t_on=0.5, t_off=0.5):
        # print "LedManager: Start blinking led", ledname, "({}s,{},s)".format(t_on, t_off)
        assert ledname in self.__leds
        self.__leds[ledname].start_blinking(t_on, t_off)

    def led_stop_blinking(self, ledname):
        # print "LedManager: Stop blinking led", ledname
        assert ledname in self.__leds
        self.__leds[ledname].stop_blinking()

    def led_lamp(self, ledname, intervals):
        assert ledname in self.__leds

        int_str = ""
        for t in intervals:
            int_str = int_str + "{}s,".format(t)
        # print "LedManager: Lamp led", ledname, "(", int_str, ")"

        if self.__leds[ledname].status == LED.BLINKING:
            # print bcolors.WARNING+"LedManager: warning - led was blinking. stopping..."+bcolors.ENDC
            self.__leds[ledname].stop_blinking()
        self.__leds[ledname].lamp(intervals)

