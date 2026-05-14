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
ultrasonic = DistanceSensor(echo=24, trigger=23)

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

print("Autonomous Navigation Test Started")
print("Press q to quit")

# =========================
# MAIN LOOP
# =========================

try:
    while True:
        frame = picam2.capture_array()

        distance = ultrasonic.distance * 100
        ir_value = ir_sensor.value

        detected_person = False
        detected_stop_sign = False

        results = model(frame, verbose=False)

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if class_id in TRAFFIC_CLASSES and confidence > 0.45:
                    label = TRAFFIC_CLASSES[class_id]
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

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

                    if label == "person":
                        detected_person = True

                    if label == "stop sign":
                        detected_stop_sign = True

        print(f"\nDistance: {distance:.2f} cm")
        print(f"IR Sensor: {ir_value}")

        # =========================
        # DECISION LOGIC
        # =========================

        if ir_value == 0:
            print("ACTION: STOP")
            print("ACTION: REVERSE A LITTLE")
            print("ACTION: TURN RIGHT")

        elif distance < 10:
            print("ACTION: STOP")
            print("ACTION: REVERSE A LITTLE")
            print("ACTION: TURN LEFT")

        elif distance < 25:
            print("ACTION: SLOW DOWN")
            print("ACTION: PREPARE TO TURN")

        elif detected_person:
            print("ACTION: STOP FOR PERSON")

        elif detected_stop_sign:
            print("ACTION: STOP FOR STOP SIGN")

        else:
            print("ACTION: MOVE FORWARD")

        cv2.imshow("Autonomous Navigation Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("Program stopped")

finally:
    picam2.stop()
    cv2.destroyAllWindows()
