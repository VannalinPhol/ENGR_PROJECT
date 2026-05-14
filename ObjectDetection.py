from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import time

# Load pretrained YOLO model
model = YOLO("yolov8n.pt")

# Traffic-related classes
TRAFFIC_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    6: "train",
    7: "truck",
    9: "traffic light",
    11: "stop sign",
}

# Different colors for each object
COLORS = {
    0: (0, 255, 0),        # person = green
    1: (255, 0, 0),        # bicycle = blue
    2: (0, 0, 255),        # car = red
    3: (255, 255, 0),      # motorcycle = cyan
    5: (255, 0, 255),      # bus = purple
    6: (0, 255, 255),      # train = yellow
    7: (128, 0, 255),      # truck = orange
    9: (255, 255, 255),    # traffic light = white
    11: (0, 165, 255),     # stop sign = orange-yellow
}

# Start Raspberry Pi camera
picam2 = Picamera2()

picam2.configure(
    picam2.create_preview_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)

picam2.start()

time.sleep(2)

print("Traffic Object Detection Started!")
print("Press q to quit")

while True:

    # Capture frame
    frame = picam2.capture_array()

    # Run YOLO detection
    results = model(frame, verbose=False)

    # Loop through results
    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # Only detect traffic objects
            if class_id in TRAFFIC_CLASSES and confidence > 0.45:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                label = TRAFFIC_CLASSES[class_id]

                # Get color
                color = COLORS[class_id]

                # Draw rectangle
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                # Draw label
                cv2.putText(
                    frame,
                    f"{label} {confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

    # Show camera window
    cv2.imshow("Traffic Detection", frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
picam2.stop()
cv2.destroyAllWindows()