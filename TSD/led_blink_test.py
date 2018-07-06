
import RPi.GPIO as IO
import time 
IO.setmode(IO.BOARD)       # programming the GPIO by BOARD pin numbers, GPIO21 is called as PIN40
IO.setup(40,IO.OUT)             # initialize digital pin40 as an output.
while True:
  IO.output(40,IO.HIGH)                      # turn the LED on (making the voltage level HIGH)
  raw_input("press any key...")
  IO.output(40,IO.LOW)                      # turn the LED on (making the voltage level HIGH)                           # turn the LED off (making all the output pins LOW)
  raw_input("press any key...")
