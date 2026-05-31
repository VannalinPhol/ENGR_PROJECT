from gpiozero import DistanceSensor
from time import sleep

# GPIO pins
sensor = DistanceSensor(
    echo=6,
    trigger=5,
    max_distance=4,   # 4 meters
    threshold_distance=0.1
)

print("Ultrasonic Sensor Test Started")

try:
    while True:
        distance_cm = sensor.distance * 100

        # Ignore very small noise readings
        if distance_cm < 2:
            print("No object detected")
        else:
            print(f"Distance: {distance_cm:.1f} cm")

        sleep(0.5)

except KeyboardInterrupt:
    print("\nTest stopped")