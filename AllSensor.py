from picamera2 import Picamera2
from ultralytics import YOLO
from gpiozero import DistanceSensor, DigitalInputDevice
import cv2
import time

# =========================
# SENSOR SETUP
# =========================

# IR Sensor
# OUT connected to GPIO5
ir_sensor = DigitalInputDevice(5)

# Ultrasonic Sensor
# TRIG -> GPIO23
# ECHO -> GPIO24
ultrasonic = DistanceSensor(
    echo=24,
    trigger=23
)

# =========================
# YOLO MODEL
# =========================

model = YOLO("yolov8n.pt")

TRAFFIC_CLASSES = {
    0: "person",
    11: "stop sign",
}

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

time.sleep(2)

print("Autonomous Navigation Started")
print("Press q to quit")

# =========================
# MAIN LOOP
# =========================

try:

    while True:

        # -------------------------
        # Capture camera frame
        # -------------------------

        frame = picam2.capture_array()

        # -------------------------
        # Read sensors
        # -------------------------

        distance = ultrasonic.distance * 100
        ir_value = ir_sensor.value

        # -------------------------
        # YOLO Detection
        # -------------------------

        results = model(frame, verbose=False)

        detected_person = False
        detected_stop_sign = False

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if class_id in TRAFFIC_CLASSES and confidence > 0.45:

                    label = TRAFFIC_CLASSES[class_id]

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Draw rectangle
                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )

                    # Draw label
                    cv2.putText(
                        frame,
                        f"{label} {confidence:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

                    if label == "person":
                        detected_person = True

                    if label == "stop sign":
                        detected_stop_sign = True

        # -------------------------
        # PATH DETECTION
        # -------------------------

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        _, thresh = cv2.threshold(
            blur,
            60,
            255,
            cv2.THRESH_BINARY_INV
        )

        height, width = thresh.shape

        mask = thresh[int(height * 0.7):height, 0:width]

        M = cv2.moments(mask)

        path_position = "NONE"

        if M['m00'] > 0:

            cx = int(M['m10'] / M['m00'])

            if cx < (width // 2) - 40:
                path_position = "LEFT"

            elif cx > (width // 2) + 40:
                path_position = "RIGHT"

            else:
                path_position = "CENTER"

        # -------------------------
        # AUTONOMOUS LOGIC
        # -------------------------

        print(f"\nDistance: {distance:.2f} cm")
        print(f"IR Sensor: {ir_value}")
        print(f"Path Position: {path_position}")

        # IR emergency obstacle
        if ir_value == 0:

            print("ACTION: STOP")
            print("ACTION: REVERSE A LITTLE")
            print("ACTION: TURN RIGHT")

        # Ultrasonic obstacle
        elif distance < 10:

            print("ACTION: STOP")
            print("ACTION: REVERSE A LITTLE")
            print("ACTION: TURN LEFT")

        # Slow down zone
        elif distance < 25:

            print("ACTION: SLOW DOWN")
            print("ACTION: PREPARE TO TURN")

        # Person detected
        elif detected_person:

            print("ACTION: STOP FOR PERSON")

        # Stop sign detected
        elif detected_stop_sign:

            print("ACTION: STOP FOR STOP SIGN")

        # Camera path navigation
        elif path_position == "LEFT":

            print("ACTION: TURN LEFT SLIGHTLY")

        elif path_position == "RIGHT":

            print("ACTION: TURN RIGHT SLIGHTLY")

        elif path_position == "CENTER":

            print("ACTION: MOVE FORWARD")

        else:

            print("ACTION: STOP")
            print("ACTION: SEARCH FOR PATH")

        # -------------------------
        # Show camera window
        # -------------------------

        cv2.imshow("Autonomous Navigation", frame)

        # Quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:

    print("Program stopped")

finally:

    picam2.stop()

    cv2.destroyAllWindows()