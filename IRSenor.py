from gpiozero import DigitalInputDevice
from time import sleep

sensor = DigitalInputDevice(17)

last_value = None

print("Calibrating IR sensor...")
print("Turn the blue knob slowly until it changes when object is near.")

while True:
    value = sensor.value

    if value != last_value:
        print("Raw sensor value:", value)

        if value == 0:
            print("Object detected")
        else:
            print("No object")

        last_value = value

    sleep(0.1)