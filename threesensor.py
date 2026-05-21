# Camera YOLO + Ultrasonic + DC Motor
# TB6612FNG + Raspberry Pi BOARD pin mode

from time import sleep, time
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import numpy as np

# =========================
# GPIO SETUP
# =========================

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Motor pins
PWMA = 12
AIN1 = 16
AIN2 = 18
STBY = 22

# Ultrasonic pins
TRIG = 29
ECHO = 31

GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

pwmFreq = 100
pwma = GPIO.PWM(PWMA, pwmFreq)
pwma.start(0)

# =========================
# MOTOR FUNCTIONS
# =========================

def motor_forward(speed):
    GPIO.output(STBY, GPIO.HIGH)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    pwma.ChangeDutyCycle(speed)

def motor_stop():
    pwma.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

# =========================
# ULTRASONIC FUNCTION
# =========================

def get_distance():
    GPIO.output(TRIG, GPIO.LOW)
    sleep(0.05)

    GPIO.output(TRIG, GPIO.HIGH)
    sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    start_time = time()
    timeout = start_time + 0.03

    while GPIO.input(ECHO) == 0:
        start_time = time()
        if start_time > timeout:
            return None

    stop_time = time()
    timeout = stop_time + 0.03

    while GPIO.input(ECHO) == 1:
        stop_time = time()
        if stop_time > timeout:
            return None

    elapsed = stop_time - start_time
    distance = (elapsed * 34300) / 2
    return distance

# =========================
# YOLO SETUP
# =========================

model = YOLO("yolov8n.pt")

OBJECT_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    9: "traffic light"
}

# =========================
# TRAFFIC LIGHT COLOR CHECK
# =========================

def detect_traffic_light_color(crop):
    if crop.size == 0:
        return "unknown"

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    red1 = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255))
    red2 = cv2.inRange(hsv, (170, 70, 50), (180, 255, 255))
    red_mask = red1 + red2

    green_mask = cv2.inRange(hsv, (40, 70, 50), (90, 255, 255))

    red_count = cv2.countNonZero(red_mask)
    green_count = cv2.countNonZero(green_mask)

    if red_count > green_count and red_count > 20:
        return "red traffic light"
    elif green_count > red_count and green_count > 20:
        return "green traffic light"
    else:
        return "traffic light"

# =========================
# CAMERA SETUP
# =========================

picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)
picam2.start()
sleep(2)

print("System started. Press q to quit.")

# =========================
# MAIN LOOP
# =========================

try:
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        distance = get_distance()

        detected_objects = []
        red_light = False
        green_light = False

        results = model(frame, verbose=False)

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if class_id in OBJECT_CLASSES and confidence > 0.45:
                    label = OBJECT_CLASSES[class_id]
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if label == "traffic light":
                        crop = frame[y1:y2, x1:x2]
                        label = detect_traffic_light_color(crop)

                        if label == "red traffic light":
                            red_light = True
                        elif label == "green traffic light":
                            green_light = True

                    detected_objects.append(label)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{label} {confidence:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

        if distance is None:
            print("No ultrasonic reading → STOP")
            motor_stop()
            continue

        print(f"Distance: {distance:.1f} cm")
        print("Detected:", detected_objects)

        # =========================
        # DECISION LOGIC
        # =========================

        if distance < 15:
            print("ACTION: Very close object → STOP")
            motor_stop()

        elif red_light:
            print("ACTION: Red traffic light medium/far → SLOW")
            motor_forward(30)

        elif "person" in detected_objects:
            print("ACTION: Person detected → SLOW")
            motor_forward(30)

        elif (
            "car" in detected_objects or
            "truck" in detected_objects or
            "bus" in detected_objects or
            "bicycle" in detected_objects or
            "motorcycle" in detected_objects
        ):
            print("ACTION: Vehicle detected → SLOW")
            motor_forward(40)

        elif green_light and distance > 40:
            print("ACTION: Green light and clear → FAST")
            motor_forward(100)

        elif len(detected_objects) == 0 and distance > 40:
            print("ACTION: No object and clear → FAST")
            motor_forward(100)

        else:
            print("ACTION: Default caution → SLOW")
            motor_forward(40)

        cv2.imshow("YOLO + Ultrasonic + Motor", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        sleep(0.1)

except KeyboardInterrupt:
    print("Program stopped")

finally:
    motor_stop()
    GPIO.output(STBY, GPIO.LOW)
    pwma.stop()
    GPIO.cleanup()
    picam2.stop()
    cv2.destroyAllWindows()