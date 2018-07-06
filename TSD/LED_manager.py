import RPi.GPIO as IO
import time
import threading


class LED(object):
    SOURCE = True;  # TURNS ON IF PIN HIGH
    DRAIN = False;  # TURNS ON IF PIN LOW

    ON = 1;
    OFF = 0;
    BLINKING = -1;

    def __init__(self, pin, conf):
        print "Creating new LED on pin {} as {}".format(pin,conf)
        self.pin = pin
        self.conf = conf
        self.status = not conf
        IO.setup(pin, IO.OUT)
        IO.output(pin, IO.LOW if conf else IO.HIGH)

    def turn_on(self):
        print "LED: Turning ON pin", self.pin
        IO.output(self.pin, IO.HIGH if self.conf else IO.LOW)
        self.status = LED.ON

    def turn_off(self):
        print "LED: Turning OFF pin", self.pin
        IO.output(self.pin, IO.HIGH if self.conf else IO.LOW)
        self.status = LED.OFF

    def start_blinking(self, t_on, t_off):
        print "LED: Starting to blink pin", self.pin
        if self.status != LED.BLINKING:
            self.__stop_blnk = threading.Event()
            blnkThr = threading.Thread(target=self.__blink, args=(t_on, t_off, self.__stop_blnk))

    def __blink(self, t_on, t_off, stop_event):
        while (not stop_event.is_set()):
            self.__turn_on()
            stop_event.wait(t_on)
            self.__turn_off()
            stop_event.wait(t_off)
            pass

    def stop_blinking(self):
        if self.status == LED.BLINKING:
            print "LED: Stopping to blink pin", self.pin
            self.__stop_blnk.set()
            self.turn_off()

    def toggle(self):
        print "LED: toggle pin", self.pin
        self.turn_off() if self.status == LED.ON else self.turn_on()


    def lamp(self, *intervals):
        if self.status != LED.BLINKING:
            print "LED: Starting thread to lamp pin", self.pin
            threading.Thread(target=self.__lamp_thread, args=(intervals))
        else:
            print "LED: warning - Led BLINKINg"

    def __lamp_thread(self, *intervals):

        prev_stat = self.status #seve previous status
        self.turn_off()  #first turn off, then start the sequence
        time.sleep(0.5)
        for t in intervals:
            self.toggle()
            time.sleep(t)
        # restore previous status
        self.turn_off() if prev_stat == LED.OFF else self.turn_on()

class LedManager(object):

    def __init__(self, *leds):
        print "LedManager: Starting with ", leds
        IO.setmode(IO.BOARD)
        self.__leds = {}
        for led in leds:
            self.add_led(led[0], led[1], led[2])

    def add_led(self, name, pin, conf):
        assert name not in self.__leds
        print "LedManager: Adding led ", name, "at pin", pin, "in conf", conf
        self.__leds[name] = LED(pin, conf)

    def led_turn_on(self, ledname):
        """
        :param ledname: name of the led in ledmanager
        :return: nothing
        """
        assert ledname not in self.__leds
        print "LedManager: Turning led", ledname, "ON"
        if ledname in self.__leds:
            if self.__leds[ledname].status == LED.BLINKING:
                print "LedManager: warning - led was blinking. stopping..."
                self.__leds[ledname].stop_blinking()
            self.__leds[ledname].turn_on()

    def led_turn_off(self, ledname):
        """
        :param ledname: name of the led in ledmanager
        :return: nothing
        """
        print "LedManager: Turning led", ledname, "OFF"
        assert ledname not in self.__leds
        if ledname in self.__leds:
            if self.__leds[ledname].status == LED.BLINKING:
                print "LedManager: warning - led was blinking. stopping..."
                self.__leds[ledname].stop_blinking()
            self.__leds[ledname].turn_off()

    def led_start_blinking(self, ledname, t_on=0.5, t_off=0.5):
        print "LedManager: Start blinking led", ledname, "({}s,{},s)".format(t_on, t_off)
        assert ledname in self.__leds
        self.__leds[ledname].start_blinking(t_on, t_off)

    def led_stop_blinking(self, ledname):
        print "LedManager: Stop blinking led", ledname
        assert ledname in self.__leds
        self.__leds[ledname].stop_blinking()

    def led_lamp(self, ledname, *intervals):
        for t in intervals:
            int_str = int_str + "{}s,".format(t)
        print "LedManager: Lamp led", ledname, "(", int_str, ")"
        assert ledname in self.__leds
        if self.__leds[ledname].status == LED.BLINKING:
            print "LedManager: warning - led was blinking. stopping..."
            self.__leds[ledname].stop_blinking()
        self.__leds[ledname].lamp(*intervals)

