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
        self.pin = pin
        self.conf = conf
        self.status = not conf
        IO.setup(pin, IO.OUT)
        IO.output(pin, IO.LOW if conf else IO.HIGH)

    def turn_on(self):
        IO.output(self.pin, IO.HIGH if self.conf else IO.LOW)
        self.status = LED.ON

    def turn_off(self):
        IO.output(self.pin, IO.HIGH if self.conf else IO.LOW)
        self.status = LED.OFF

    def start_blinking(self, t_on, t_off):
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
            self.__stop_blnk.set()
            self.turn_off()

    def trigger(self):
        self.turn_off() if self.status == LED.ON else self.turn_on()

    def lamp(self, *intervals):
        if self.status != LED.BLINKING:
            threading.Thread(target=self.__lamp_thread, args=(intervals))

    def __lamp_thread(self, *intervals):
        prev_stat = self.status #seve previous status
        self.turn_off()  #first turn off, then start the sequence
        time.sleep(0.5)
        for t in intervals:
            self.trigger()
            time.sleep(t)
        # restore previous status
        self.turn_off() if prev_stat == LED.OFF else self.turn_on()

class LedManager(object):

    def __init__(self, *leds):
        IO.setmode(IO.BOARD)
        self.__leds = {}
        for led in leds:
            self.add_led(led[1], led[2], led[3])

    def add_led(self, name, pin, conf):
        assert name not in self.__leds
        self.__leds[name] = LED(pin, conf)

    def led_turn_on(self, ledname):
        """
        :param ledname: name of the led in ledmanager
        :return: nothing
        """
        assert name not in self.__leds
        if ledname in self.__leds:
            if self.__leds[ledname].status == LED.BLINKING:
                self.__leds[ledname].stop_blinking()
            self.__leds[ledname].turn_on()

    def led_turn_off(self, ledname):
        """
        :param ledname: name of the led in ledmanager
        :return: nothing
        """
        assert name not in self.__leds
        if ledname in self.__leds:
            if self.__leds[ledname].status == LED.BLINKING:
                self.__leds[ledname].stop_blinking()
            self.__leds[ledname].turn_off()

    def led_start_blinking(self, ledname, t_on=0.5, t_off=0.5):
        assert ledname in self.__leds
        self.__leds[ledname].start_blinking(t_on, t_off)

    def led_stop_blinking(self, ledname):
        assert ledname in self.__leds
        self.__leds[ledname].stop_blinking()

    def led_lamp(self, ledname, *intervals):
        assert ledname in self.__leds
        if self.__leds[ledname].status == LED.BLINKING:
            self.__leds[ledname].stop_blinking()
        self.__leds[ledname].lamp(*intervals)

