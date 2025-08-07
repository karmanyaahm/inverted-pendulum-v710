# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import math
import time
import board
import adafruit_mlx90393
from burst import FastXY

print("LA")
i2c = board.I2C()  # uses board.SCL and board.SDA
time.sleep(.1)
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
print("LA")
SENSOR = FastXY(i2c, address=0x18, oversampling = 3, filt=5,gain=adafruit_mlx90393.GAIN_1X)
SENSOR.start_burst()
print("LA")
lasttime = time.monotonic()
print("LA")
while True:
    MX, MY = SENSOR.burst_xy()
    print("[{:.1f}, {:.1f}]".format(time.monotonic(), 1/(time.monotonic() - lasttime)), end = ":\t" )
    lasttime = time.monotonic()
    print("X: {:.1f} uT".format(MX), end = "\t")
    print("Y: {:.1f} uT".format(MY), end = "\t")
    print('theta-xy-plane: ')
    print('{:.1f}'.format(math.degrees(math.atan2(MY,MX))))
    # Display the status field if an error occured, etc.
    if SENSOR.last_status > adafruit_mlx90393.STATUS_OK:
        SENSOR.display_status()
        print(SENSOR.last_status)
