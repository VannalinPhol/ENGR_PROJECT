# Camera YOLO + Ultrasonic + DC Motor + Servo Motor
# TB6612FNG + Raspberry Pi BOARD pin mode

from time import sleep, time
import RPi.GPIO as GPIO
from gpiozero import Servo
from picamera2 import Picamera2
from ultralytics import YOLO
import cv2

# =========================
# GPIO SETUP
# =========================

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# DC Motor pins
PWMA = 12
AIN1 = 16
AIN2 = 18
STBY = 22

# Ultrasonic pins
TRIG = 29
ECHO = 31

# Servo pin - GPIO13, physical pin 33
SERVO_PIN = 13

GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

pwma = GPIO.PWM(PWMA, 100)
pwma.start(0)

# Servo setup
my_servo = Servo(
    SERVO_PIN,
    min_pulse_width=0.001,
    max_pulse_width=0.002
)

# =========================
# SERVO FUNCTIONS
# =========================

def move_servo_angle(angle):
    value = (angle / 90) - 1
    my_servo.value = value
    sleep(0.3)

def servo_center():
    print("SERVO: CENTER")
    move_servo_angle(90)

def servo_left():
    print("SERVO: TURN LEFT")
    move_servo_angle(0)

def servo_right():
    print("SERVO: TURN RIGHT")
    move_servo_angle(180)

# =========================
# DC MOTOR FUNCTIONS
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
    yellow_mask = cv2.inRange(hsv, (20, 70, 50), (35, 255, 255))

    red_count = cv2.countNonZero(red_mask)
    green_count = cv2.countNonZero(green_mask)
    yellow_count = cv2.countNonZero(yellow_mask)

    if red_count > green_count and red_count > yellow_count and red_count > 20:
        return "red traffic light"
    elif green_count > red_count and green_count > yellow_count and green_count > 20:
        return "green traffic light"
    elif yellow_count > red_count and yellow_count > green_count and yellow_count > 20:
        return "yellow traffic light"
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
    servo_center()

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        frame_width = frame.shape[1]
        distance = get_distance()

        detected_objects = []

        red_light = False
        green_light = False
        yellow_light = False

        turn_left_sign = False
        turn_right_sign = False

        object_position = "center"

        results = model(frame, verbose=False)

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if class_id in OBJECT_CLASSES and confidence > 0.45:
                    label = OBJECT_CLASSES[class_id]
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    object_center_x = (x1 + x2) / 2

                    if object_center_x < frame_width / 3:
                        object_position = "left"
                    elif object_center_x > frame_width * 2 / 3:
                        object_position = "right"
                    else:
                        object_position = "center"

                    if label == "traffic light":
                        crop = frame[y1:y2, x1:x2]
                        label = detect_traffic_light_color(crop)

                        if label == "red traffic light":
                            red_light = True
                        elif label == "green traffic light":
                            green_light = True
                        elif label == "yellow traffic light":
                            yellow_light = True

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
            servo_center()
            continue

        print(f"Distance: {distance:.1f} cm")
        print("Detected:", detected_objects)
        print("Object position:", object_position)

        # =========================
        # DECISION LOGIC
        # =========================

        if distance < 15:
            print("ACTION: Very close object → STOP")
            motor_stop()
            servo_center()

        elif red_light:
            print("ACTION: Red traffic light → STOP")
            motor_stop()
            servo_center()

        elif yellow_light:
            print("ACTION: Yellow traffic light → SLOW")
            motor_forward(30)
            servo_center()

        elif green_light:
            print("ACTION: Green traffic light → FAST")
            motor_forward(100)
            servo_center()

        elif "person" in detected_objects:
            if distance < 15:
                print("ACTION: Person close → STOP")
                motor_stop()
            elif distance > 40:
                print("ACTION: Person far/clear → FAST")
                motor_forward(100)
            else:
                print("ACTION: Person medium/far → SLOW")
                motor_forward(30)

            servo_center()

        elif (
            "car" in detected_objects or
            "truck" in detected_objects or
            "bus" in detected_objects or
            "bicycle" in detected_objects or
            "motorcycle" in detected_objects
        ):
            if distance < 15:
                print("ACTION: Vehicle close → STOP")
                motor_stop()
                servo_center()

            elif 15 <= distance <= 40:
                print("ACTION: Vehicle medium → SLOW + AVOID")

                motor_forward(40)

                if object_position == "left":
                    servo_right()
                elif object_position == "right":
                    servo_left()
                else:
                    servo_left()

                sleep(0.8)
                servo_center()

            elif distance > 40:
                print("ACTION: Vehicle far/clear → FAST")
                motor_forward(100)
                servo_center()

        elif turn_left_sign:
            if 15 <= distance <= 40:
                print("ACTION: Turn left sign → TURN LEFT then forward")
                motor_forward(40)
                servo_left()
                sleep(1)
                servo_center()
            else:
                motor_forward(100)
                servo_center()

        elif turn_right_sign:
            if 15 <= distance <= 40:
                print("ACTION: Turn right sign → TURN RIGHT then forward")
                motor_forward(40)
                servo_right()
                sleep(1)
                servo_center()
            else:
                motor_forward(100)
                servo_center()

        elif len(detected_objects) == 0 and distance > 40:
            print("ACTION: No object and clear → FAST")
            motor_forward(100)
            servo_center()

        else:
            print("ACTION: Unknown / uncertain case → SLOW")
            motor_forward(40)
            servo_center()

        cv2.imshow("YOLO + Ultrasonic + DC Motor + Servo", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        sleep(0.1)

except KeyboardInterrupt:
    print("Program stopped")

finally:
    motor_stop()
    servo_center()
    my_servo.value = None
    GPIO.output(STBY, GPIO.LOW)
    pwma.stop()
    GPIO.cleanup()
    picam2.stop()
    cv2.destroyAllWindows()