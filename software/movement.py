import digitalio
import board
import time
import signal
import sys

left = digitalio.DigitalInOut(board.D12)
right = digitalio.DigitalInOut(board.D13)

left.switch_to_input()
right.switch_to_input()

def signal_handler(sig, frame):
    right.pull = digitalio.Pull.DOWN
    left.pull = digitalio.Pull.DOWN
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def move(proportion: float, pin):
    if pin == right:
        altpin = left
    else:
        altpin = right

    altpin.pull = digitalio.Pull.DOWN

    on_time = proportion * 0.005
    off_time = (1 - proportion) * 0.005

    pin.pull = digitalio.Pull.UP
    time.sleep(on_time)

    pin.pull = digitalio.Pull.DOWN
    time.sleep(off_time)

left_time = 3
right_time = 3

# Or, after left_to_input
while True:
    for i in range(100):
        move(0.5, right)
    for i in range(100):
        move(0.5, left)

signal.pause()