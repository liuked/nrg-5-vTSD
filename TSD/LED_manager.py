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
        status = LED.ON

    def turn_off(self):
        IO.output(self.pin, IO.HIGH if self.conf else IO.LOW)
        status = LED.OFF

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

class LedManager(object):

    def __init__(self, *leds):
        IO.setmode(IO.BOARD)
        self.leds = {}
        for led in leds:
            self.add_led(led[1], led[2], led[3])

    def add_led(self, name, pin, conf):
        self.leds[name] = LED(pin, conf)
        s

    def turn_on(self, ledname):
        """

        :param ledname: name of the led in ledmanager
        :return: nothing
        """
        if ledname in self.leds:
            ledname.turn_on()

    def led_start_blinking(self, led):
        assert led in self.leds
        led.start_blinking(0.5, 0.5)

    def led_stop_blinking(self, led):
        assert led in self.leds
        led.stop_blinking()