from gpiozero import DistanceSensor
from time import sleep

sensor = DistanceSensor(
    echo=24,
    trigger=23
)

while True:
    distance = sensor.distance * 100
    print(f"Distance: {distance:.2f} cm")

    sleep(0.5)