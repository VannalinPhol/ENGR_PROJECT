import tkinter as tk
import time
import cv2
from gpiozero import DistanceSensor
from picamera2 import Picamera2
from ultralytics import YOLO

# =========================
# ULTRASONIC SENSOR
# =========================

TRIGGER_PIN = 5
ECHO_PIN = 6

STOP_DISTANCE = 15
SLOW_DISTANCE = 40
MAX_RANGE_CM = 400

sensor = DistanceSensor(
    echo=ECHO_PIN,
    trigger=TRIGGER_PIN,
    max_distance=MAX_RANGE_CM / 100,
    queue_len=5,
    partial=True
)

def get_distance():
    try:
        d = sensor.distance
        if d is None:
            return None
        return round(d * 100, 1)
    except Exception:
        return None


# =========================
# YOLO CAMERA
# =========================

model = YOLO("yolov8n.pt")

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

COLORS = {
    0: (0, 255, 0),
    1: (255, 0, 0),
    2: (0, 0, 255),
    3: (255, 255, 0),
    5: (255, 0, 255),
    6: (0, 255, 255),
    7: (128, 0, 255),
    9: (255, 255, 255),
    11: (0, 165, 255),
}

picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)
picam2.start()
time.sleep(2)


# =========================
# GUI
# =========================

WIDTH = 1400
HEIGHT = 800

root = tk.Tk()
root.title("Autonomous Navigation Dashboard")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.configure(bg="#050b12")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#050b12", highlightthickness=0)
canvas.pack()

last_distance = 100
stop_until = 0
camera_img = None
last_detected_object = "None"


def get_status(distance, person_detected, forced_stop=False):
    if distance is None:
        return "ERROR", "#94a3b8", "Sensor error", 0

    if forced_stop:
        return "STOP", "#ff3b30", "Waiting 3 seconds", 0

    if person_detected and distance < STOP_DISTANCE:
        return "STOP", "#ff3b30", "Person close", 0

    if person_detected and distance < SLOW_DISTANCE:
        return "SLOW", "#ffd60a", "Person medium distance", 25

    if distance < STOP_DISTANCE:
        return "STOP", "#ff3b30", "Object close", 0

    if distance < SLOW_DISTANCE:
        return "SLOW", "#ffd60a", "Object nearby", 25

    return "FAST", "#30ff5a", "Path clear", 60


def detect_objects():
    global last_detected_object

    frame = picam2.capture_array()

    # Rotate camera 180 degrees
    frame = cv2.rotate(frame, cv2.ROTATE_180)

    results = model(frame, verbose=False)

    person_detected = False
    detected_names = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            if class_id in TRAFFIC_CLASSES and confidence > 0.45:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = TRAFFIC_CLASSES[class_id]
                color = COLORS[class_id]

                detected_names.append(label)

                if class_id == 0:
                    person_detected = True

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"{label} {confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

    if detected_names:
        last_detected_object = ", ".join(sorted(set(detected_names)))
    else:
        last_detected_object = "None"

    return frame, person_detected


def cv2_to_tk(frame):
    frame = cv2.resize(frame, (760, 520))
    success, encoded = cv2.imencode(".ppm", frame)

    if not success:
        return None

    return tk.PhotoImage(data=encoded.tobytes())


def draw_gauge(cx, cy, radius, value, max_value, title, unit, color):
    canvas.create_oval(
        cx - radius,
        cy - radius,
        cx + radius,
        cy + radius,
        outline="#1f2937",
        width=16
    )

    canvas.create_oval(
        cx - radius + 25,
        cy - radius + 25,
        cx + radius - 25,
        cy + radius - 25,
        outline="#111827",
        width=3
    )

    angle_extent = int((value / max_value) * 270)

    canvas.create_arc(
        cx - radius + 10,
        cy - radius + 10,
        cx + radius - 10,
        cy + radius - 10,
        start=135,
        extent=-angle_extent,
        outline=color,
        width=12,
        style="arc"
    )

    canvas.create_text(
        cx,
        cy - 30,
        text=str(value),
        fill="white",
        font=("Arial", 54, "bold")
    )

    canvas.create_text(
        cx,
        cy + 25,
        text=unit,
        fill="#9ca3af",
        font=("Arial", 18)
    )

    canvas.create_text(
        cx,
        cy + 85,
        text=title,
        fill=color,
        font=("Arial", 18, "bold")
    )


def draw_panel(x1, y1, x2, y2, title):
    canvas.create_rectangle(
        x1,
        y1,
        x2,
        y2,
        fill="#071521",
        outline="#1e3a4f",
        width=2
    )

    canvas.create_text(
        x1 + 20,
        y1 + 25,
        text=title,
        fill="white",
        font=("Arial", 13, "bold"),
        anchor="w"
    )


def draw_dashboard(frame, distance, person_detected, status, color, message, speed):
    global camera_img

    canvas.delete("all")

    # Header
    canvas.create_rectangle(0, 0, WIDTH, 80, fill="#070b10", outline="#111827")
    canvas.create_text(
        WIDTH // 2,
        40,
        text="AUTONOMOUS NAVIGATION DASHBOARD",
        fill="white",
        font=("Arial", 24, "bold")
    )

    canvas.create_oval(1210, 32, 1225, 47, fill="#22c55e", outline="")
    canvas.create_text(
        1240,
        40,
        text="SYSTEM ACTIVE",
        fill="#bbf7d0",
        font=("Arial", 14, "bold"),
        anchor="w"
    )

    # Centre camera feed
    draw_panel(320, 100, 1080, 640, "LIVE YOLO CAMERA FEED")

    camera_img = cv2_to_tk(frame)

    if camera_img:
        canvas.create_image(700, 385, image=camera_img)

    # Left speed gauge
    draw_gauge(
        cx=160,
        cy=340,
        radius=140,
        value=speed,
        max_value=100,
        title="SPEED",
        unit="km/h",
        color=color
    )

    # Right distance gauge
    display_distance = 0 if distance is None else int(distance)

    draw_gauge(
        cx=1235,
        cy=340,
        radius=140,
        value=min(display_distance, 100),
        max_value=100,
        title="ULTRASONIC",
        unit="cm",
        color=color
    )

    canvas.create_text(
        1235,
        520,
        text=f"{display_distance} cm",
        fill=color,
        font=("Arial", 26, "bold")
    )

    # Bottom status panels
    draw_panel(40, 670, 350, 770, "CURRENT STATUS")
    canvas.create_text(70, 720, text=status, fill=color,
                       font=("Arial", 28, "bold"), anchor="w")
    canvas.create_text(70, 750, text=message, fill="#cbd5e1",
                       font=("Arial", 13), anchor="w")

    draw_panel(380, 670, 690, 770, "DETECTED OBJECT")
    canvas.create_text(410, 720, text=last_detected_object, fill="white",
                       font=("Arial", 22, "bold"), anchor="w")

    draw_panel(720, 670, 1030, 770, "CAMERA")
    camera_status = "PERSON DETECTED" if person_detected else "CLEAR"
    canvas.create_text(750, 720, text=camera_status, fill=color,
                       font=("Arial", 22, "bold"), anchor="w")

    draw_panel(1060, 670, 1360, 770, "CONTROL MODE")
    canvas.create_text(1090, 720, text="AUTONOMOUS", fill="#38bdf8",
                       font=("Arial", 22, "bold"), anchor="w")


def update():
    global stop_until, last_distance

    now = time.time()

    distance = get_distance()

    if distance is not None:
        last_distance = distance
    else:
        distance = last_distance

    frame, person_detected = detect_objects()

    if distance < STOP_DISTANCE and now >= stop_until:
        stop_until = now + 3

    forced_stop = now < stop_until

    status, color, message, speed = get_status(
        distance,
        person_detected,
        forced_stop
    )

    draw_dashboard(
        frame,
        distance,
        person_detected,
        status,
        color,
        message,
        speed
    )

    root.after(200, update)


def on_close():
    picam2.stop()
    cv2.destroyAllWindows()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

update()
root.mainloop()