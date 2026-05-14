from gpiozero import DigitalInputDevice
from time import sleep

# GPIO17
sensor = DigitalInputDevice(17)

print("IR Sensor Test Started")

while True:

    if sensor.value == 0:
        print("Object detected!")
    else:
        print("No object detected")

    sleep(0.5)