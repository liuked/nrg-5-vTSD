from LED_manager import all 

leds = LedManager([("G1", 40, LED.SOURCE),
                   ("Y1", 38, LED.SOURCE),
                   ("R1", 36, LED.DRAIN),
                  ])
c = ''
while c!='e':
 leds.led_turn_on("G1")
 raw_input()
 leds.led_turn_off("G1") 
 raw_input()
 leds.les_tunr_off("R1")
 raw_input()
 leds.les_tunr_on("R1")
 c = raw_input() 
