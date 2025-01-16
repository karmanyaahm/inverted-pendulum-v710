import digitalio
import board
import time
import sys

switch = digitalio.DigitalInOut(board.D13)
altswitch = digitalio.DigitalInOut(board.D12)
switch.switch_to_input()
altswitch.switch_to_input()
# Or, after switch_to_input
while True:
    switch.pull = digitalio.Pull.UP
    time.sleep(.007)

    print(switch.value)
    switch.pull = None 
    time.sleep(.002)
