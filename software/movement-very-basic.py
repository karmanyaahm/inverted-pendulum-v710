import digitalio
import board
import time

switch = digitalio.DigitalInOut(board.D12)
altswitch = digitalio.DigitalInOut(board.D13)
altswitch.pull = None
switch.switch_to_input()
# Or, after switch_to_input
while True:
    switch.pull = digitalio.Pull.UP
    time.sleep(.01)

    print(switch.value)
    switch.pull = None 
    time.sleep(.02)
