import math
import time
import board
import digitalio
import signal
import sys
from threading import Thread, Event
from burst import FastXY
from adafruit_mlx90393 import GAIN_1X

# TOTAL EXPECTED ANGLE: 7334.25 deg
class MagnetometerReader:
    def __init__(self, i2c_address=0x18, oversampling=1, filt=5, resolution=1, gain=GAIN_1X):
        i2c = board.I2C()
        time.sleep(.1)
        self.sensor = FastXY(
            i2c, 
            address=i2c_address, 
            oversampling=oversampling, 
            filt=filt, 
            gain=gain
        )

    def read_angle(self):
        MX, MY = None, None
        while MX is None or MY is None:
            MX, MY = self.sensor.burst_xy()
        degrees = math.degrees(math.atan2(MY, MX))
        #print(f"X: {MX:.2f}, Y: {MY:.2f}, Z: {MZ:.2f}, THETA: {degrees:.2f}", end='\t\t')
        return degrees


class MotorController:
    """
    Emulates open-drain with internal pull-ups. We do software PWM in .loop().
    For forward, we'll drive the 'left' pin low; for reverse, we'll drive the 'right' pin low.
    """
    def __init__(self, left_pin, right_pin):
        self.left = digitalio.DigitalInOut(left_pin)
        self.left.switch_to_input(pull=digitalio.Pull.UP)

        self.right = digitalio.DigitalInOut(right_pin)
        self.right.switch_to_input(pull=digitalio.Pull.UP)

        self.left_limit = False
        self.right_limit = False

        self.speed = 0

    def start(self):
        thread = Thread(target=self.loop)
        thread.daemon = True
        thread.start()

    def loop(self):
        PERIOD = 100

        counter = 0
        while True:
            start_time = time.time()
            DELAY = 1e4 # Hertz
            end_time = start_time + 1 / DELAY
            assert -1.0 <= self.speed <= 1.0

            speed_abs = abs(self.speed)
            direction_is_reverse = (self.speed < 0)

            if (counter % PERIOD) < (PERIOD * speed_abs):
                motor_on = True
            else:
                motor_on = False

            if motor_on:
                if direction_is_reverse:
                    self._drive_right_low()
                    self._release_left()
                else:
                    self._drive_left_low()
                    self._release_right()
            else:
                self._drive_right_low()
                self._drive_left_low()

            if self.right.value == 0 and self.right.direction == digitalio.Direction.INPUT:
                self.right_limit = True
            else:
                self.right_limit = False

            if self.left.value == 0 and self.left.direction == digitalio.Direction.INPUT:
                self.left_limit = True
            else:
                self.left_limit = False

            curr_time = time.time()
            if curr_time <= end_time:
                time.sleep(end_time - curr_time)
            else:
                pass # print("WARNING: loop taking too long to execute.")

            counter += 1

    def set_speed(self, newspeed):
        """
        newspeed in range [-1, 1].
         - negative => reverse
         - positive => forward
         - zero => stop
        """
        print(f"speed set to {newspeed}")
        assert -1.0 <= newspeed <= 1.0
        self.speed = newspeed

    def stop(self):
        """
        Immediately stop the motor by pulling both pins high (input+pullup).
        """
        self.speed = 0
        self._drive_right_low()
        self._drive_left_low()

    def _drive_left_low(self):
        if self.left.direction != digitalio.Direction.OUTPUT or self.left.value != False:
            self.left.switch_to_output(value=False)

    def _drive_right_low(self):
        if self.right.direction != digitalio.Direction.OUTPUT or self.right.value != False:
            self.right.switch_to_output(value=False)

    def _release_left(self):
        if self.left.direction != digitalio.Direction.INPUT:
            self.left.switch_to_input(pull=digitalio.Pull.UP)

    def _release_right(self):
        if self.right.direction != digitalio.Direction.INPUT:
            self.right.switch_to_input(pull=digitalio.Pull.UP)


# import matplotlib.pyplot as plt

# Initialize lists for data logging
time_log = []
cumulative_angle_log = []
current_angle_log = []
error_log = []
pid_log = []

class MotorWithMagnetometer:
    def __init__(self, motor, magnetometer, full_length=1):
        self.motor = motor
        self.magnetometer = magnetometer
        self.prev_angle = None
        self.cumulative_angle = 0
        self.err_time = float("inf")
        self.FULL_LENGTH = full_length

    def reset(self):
        self.cumulative_angle = 0

    def move_to(self, degrees, callback=None, small_err=10, small_err_time=0.5, homing=False): # seconds
        degrees = degrees * self.FULL_LENGTH
        self.prev_angle = self.magnetometer.read_angle()
        start_time = time.time()  # Log the start time

        while True:
            if motor.left_limit:
                if homing:
                    self.reset()
                    self.prev_angle = None
                    print("JUST RESET TO 0")
                    break
            if motor.right_limit:
                print("=========================================")
                print(f"ANGLE IS {self.cumulative_angle}")
                print("+++++++++++++++++++++++++++++++++++++++++")
                if homing:
                    break
            
            current_angle = self.magnetometer.read_angle()
            if self.prev_angle is not None:
                delta_angle = current_angle - self.prev_angle
                if delta_angle > 180:
                    delta_angle -= 360
                elif delta_angle < -180:
                    delta_angle += 360
                
                if 40 <= abs(delta_angle):
                    print(f"BAD! Prev: {self.prev_angle}, Current: {current_angle}")

                self.cumulative_angle += delta_angle

                # Log data
                elapsed_time = time.time() - start_time
                time_log.append(elapsed_time)
                cumulative_angle_log.append(self.cumulative_angle)
                current_angle_log.append(current_angle)
                
                if callback:
                    error = degrees - self.cumulative_angle
                    error_log.append(error)  # Log error

                    if abs(error) < small_err:
                        if self.err_time == float("inf"):
                            self.err_time = time.time()
                        elif time.time() - self.err_time > small_err_time:
                            break

                    pid = error * 0.015
                    pid = max(-1, min(1, pid))
                    pid_log.append(pid)  # Log PID value
                    callback(pid)
                    print(f"Error={error:.2f}, Speed={pid:.2f}, CumAngle={self.cumulative_angle:.2f}, Target={degrees:.2f}")

            self.prev_angle = current_angle

        if callback:
            callback(0)

motor = MotorController(board.D12, board.D13)
magnetometer = MagnetometerReader()
stage_1_magnetometer = MagnetometerReader(i2c_address=0x19)
base_motor_with_magnetometer = MotorWithMagnetometer(motor, magnetometer, full_length = 6700)
stage_1_motor_with_magnetometer = MotorWithMagnetometer(motor, stage_1_magnetometer)


def signal_handler(sig, frame):
    motor.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def motor_step_callback(speed):
    motor.set_speed(speed)

if __name__ == "__main__":    
    motor.start()
    #motor_step_callback = print
    base_motor_with_magnetometer.move_to(-1000, callback=motor_step_callback, homing=True)
    time.sleep(2)
    base_motor_with_magnetometer.move_to(.5, callback=motor_step_callback)
    while True:
        base_motor_with_magnetometer.move_to(.45, callback=motor_step_callback)
        base_motor_with_magnetometer.move_to(.55, callback=motor_step_callback)
    #stage_1_motor_with_magnetometer.move_to(25, callback=motor_step_callback)
    time.sleep(2)

    


