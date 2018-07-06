from LED_manager import  LedManager, LED

leds = LedManager([("G1", 40, LED.SOURCE), ("Y1", 38, LED.SOURCE), ("R1", 36, LED.SOURCE)])

c = ''

while True:
    leds.led_turn_on("G1")
    raw_input()
    #led_toggle("Y1")
    leds.led_turn_off("G1")
    leds.led_start_blinking("Y1", 0.2, 0.5)
    raw_input()
    leds.led_start_blinking("R1")
    raw_input()
    leds.led_turn_on("R1")
    raw_input()
    leds.led_lamp("Y1", (0.2, 0.2, 0.8, 0.5, 0.5, 0.5, 0.5))
    raw_input()
    leds.stop_blinking("R1")


IO.cleanup()
