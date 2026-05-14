from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import time

# Load pretrained YOLO model
model = YOLO("yolov8n.pt")  # n = nano, fastest

# Start Raspberry Pi camera
picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)
picam2.start()
time.sleep(1)

print("Person detection started. Press q to quit.")

while True:
    frame = picam2.capture_array()

    # Run YOLO detection
    results = model(frame, verbose=False)

    # Draw boxes only for person class
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # COCO class 0 = person
            if class_id == 0 and confidence > 0.5:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"Person {confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

    cv2.imshow("Person Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

picam2.stop()
cv2.destroyAllWindows()