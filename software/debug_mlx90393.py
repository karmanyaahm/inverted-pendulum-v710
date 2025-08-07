import math
import time
import board
import adafruit_mlx90393

try:
    print("Starting I2C initialization...")
    i2c = board.I2C()
    print("I2C initialized successfully")
    
    print("Attempting to connect to MLX90393...")
    sensor = adafruit_mlx90393.MLX90393(
        i2c, 
        address=0x18, 
        oversampling=3, 
        filt=5,
        gain=adafruit_mlx90393.GAIN_1X
    )
    print("Sensor initialized successfully!")
    
    # Try to read data
    print("Attempting to read magnetic measurements...")
    MX, MY, MZ = sensor.magnetic
    print(f"Readings: MX={MX:.2f}, MY={MY:.2f}, MZ={MZ:.2f}")
    
except Exception as e:
    print(f"Error occurred: {str(e)}")
    print(f"Error type: {type(e)}")
    
print("Script completed")
