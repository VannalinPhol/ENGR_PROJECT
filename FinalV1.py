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
# GUI SETUP
# =========================

WIDTH = 1400
HEIGHT = 800

root = tk.Tk()
root.title("Autonomous Navigation Dashboard")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.configure(bg="#050b12")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#050b12", highlightthickness=0)
canvas.pack()

road_offset = 0
side_offset = 0

last_distance = 100
stop_until = 0
camera_img = None
last_detected_object = "None"


# =========================
# LOGIC
# =========================

def get_status(distance, person_detected, forced_stop=False):
    if distance is None:
        return "ERROR", "#94a3b8", "Sensor error", 0, "STOP"

    if forced_stop:
        return "STOP", "#ff3b30", "Waiting 3 seconds", 0, "STOP"

    if person_detected and distance < STOP_DISTANCE:
        return "STOP", "#ff3b30", "Person close", 0, "STOP"

    if person_detected and distance < SLOW_DISTANCE:
        return "SLOW", "#ffd60a", "Person medium distance", 25, "SLOW"

    if distance < STOP_DISTANCE:
        return "STOP", "#ff3b30", "Object close", 0, "STOP"

    if distance < SLOW_DISTANCE:
        return "SLOW", "#ffd60a", "Object nearby", 25, "SLOW"

    return "FAST", "#30ff5a", "Path clear", 60, "FAST"


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
    # Keep full camera view but display it smaller
    frame = cv2.resize(frame, (320, 240))

    success, encoded = cv2.imencode(".ppm", frame)

    if not success:
        return None

    return tk.PhotoImage(data=encoded.tobytes())


# =========================
# DRAWING FUNCTIONS
# =========================

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
        cx - radius + 28,
        cy - radius + 28,
        cx + radius - 28,
        cy + radius - 28,
        outline="#111827",
        width=3
    )

    angle = int((value / max_value) * 270)

    canvas.create_arc(
        cx - radius + 10,
        cy - radius + 10,
        cx + radius - 10,
        cy + radius - 10,
        start=135,
        extent=-angle,
        outline=color,
        width=12,
        style="arc"
    )

    canvas.create_text(
        cx,
        cy - 30,
        text=str(value),
        fill="white",
        font=("Arial", 50, "bold")
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


def draw_tree(x, y, scale):
    canvas.create_rectangle(
        x - 10 * scale,
        y,
        x + 10 * scale,
        y + 80 * scale,
        fill="#4b2e16",
        outline=""
    )

    canvas.create_oval(
        x - 65 * scale,
        y - 65 * scale,
        x + 65 * scale,
        y + 65 * scale,
        fill="#14532d",
        outline="#22c55e"
    )

    canvas.create_oval(
        x - 45 * scale,
        y - 110 * scale,
        x + 45 * scale,
        y - 20 * scale,
        fill="#166534",
        outline=""
    )


def draw_house(x, y, scale):
    w = 100 * scale
    h = 70 * scale

    canvas.create_rectangle(
        x - w / 2,
        y - h,
        x + w / 2,
        y,
        fill="#475569",
        outline="#94a3b8"
    )

    canvas.create_polygon(
        x - w / 2 - 10 * scale,
        y - h,
        x,
        y - h - 45 * scale,
        x + w / 2 + 10 * scale,
        y - h,
        fill="#7f1d1d",
        outline=""
    )

    canvas.create_rectangle(
        x - 35 * scale,
        y - 55 * scale,
        x - 10 * scale,
        y - 35 * scale,
        fill="#fde68a",
        outline=""
    )


def draw_navigation_scene(moving, speed_level, color, status):
    global road_offset, side_offset

    draw_panel(230, 90, 1170, 720, "AUTONOMOUS NAVIGATION VIEW")

    canvas.create_rectangle(245, 130, 1155, 705, fill="#0e2233", outline="")

    canvas.create_oval(330, 60, 1070, 700, fill="#10263a", outline="")

    # Road
    canvas.create_polygon(
        600, 155,
        800, 155,
        1110, 705,
        290, 705,
        fill="#132433",
        outline="#dbeafe",
        width=3
    )

    # Road grid
    for i in range(18):
        y = 175 + ((i * 48 + road_offset) % 520)
        scale = (y - 155) / 550

        left = 600 - 310 * scale
        right = 800 + 310 * scale

        canvas.create_line(
            left,
            y,
            right,
            y,
            fill="#1e4056",
            width=1
        )

    # Centre lane marks
    for i in range(10):
        y = 175 + ((i * 80 + road_offset) % 500)
        scale = (y - 155) / 550

        canvas.create_line(
            700,
            y,
            700,
            y + 40 * scale,
            fill="white",
            width=max(2, int(5 * scale))
        )

    # Moving trees and houses
    for i in range(10):
        y = 160 + ((i * 95 + side_offset) % 540)
        scale = max(0.25, (y - 120) / 480)

        left_x = 570 - 360 * scale
        right_x = 830 + 360 * scale

        draw_tree(left_x, y, scale)
        draw_tree(right_x, y, scale)

        if i % 3 == 0:
            draw_house(left_x - 90 * scale, y + 40 * scale, scale)
            draw_house(right_x + 90 * scale, y + 40 * scale, scale)

    # Sensor zone
    canvas.create_polygon(
        610,
        660,
        790,
        660,
        750,
        180,
        650,
        180,
        fill=color,
        stipple="gray25",
        outline=color,
        width=2
    )

    canvas.create_text(
        700,
        310,
        text=status + " ZONE",
        fill=color,
        font=("Arial", 26, "bold")
    )

    draw_big_car(700, 575)

    if moving:
        if speed_level == "FAST":
            road_offset += 40
            side_offset += 55
        elif speed_level == "SLOW":
            road_offset += 12
            side_offset += 18


def draw_big_car(cx, cy):
    canvas.create_oval(
        cx - 250,
        cy + 70,
        cx + 250,
        cy + 150,
        fill="#020617",
        outline=""
    )

    canvas.create_polygon(
        cx - 230,
        cy + 65,
        cx - 185,
        cy - 80,
        cx - 95,
        cy - 175,
        cx + 95,
        cy - 175,
        cx + 185,
        cy - 80,
        cx + 230,
        cy + 65,
        cx + 160,
        cy + 135,
        cx - 160,
        cy + 135,
        fill="#cbd5e1",
        outline="#f8fafc",
        width=3
    )

    canvas.create_polygon(
        cx - 105,
        cy - 145,
        cx + 105,
        cy - 145,
        cx + 135,
        cy - 25,
        cx - 135,
        cy - 25,
        fill="#020617",
        outline="#38bdf8",
        width=3
    )

    canvas.create_polygon(
        cx - 150,
        cy - 5,
        cx + 150,
        cy - 5,
        cx + 110,
        cy + 65,
        cx - 110,
        cy + 65,
        fill="#111827",
        outline="#475569",
        width=2
    )

    canvas.create_rectangle(
        cx - 190,
        cy + 55,
        cx + 190,
        cy + 72,
        fill="#7f1d1d",
        outline=""
    )

    canvas.create_oval(
        cx - 225,
        cy + 40,
        cx - 125,
        cy + 85,
        fill="#ff1f1f",
        outline=""
    )

    canvas.create_oval(
        cx + 125,
        cy + 40,
        cx + 225,
        cy + 85,
        fill="#ff1f1f",
        outline=""
    )


def draw_dashboard(frame, distance, person_detected, status, color, message, speed, speed_level):
    global camera_img

    canvas.delete("all")

    # Header
    canvas.create_rectangle(0, 0, WIDTH, 75, fill="#070b10", outline="#111827")

    canvas.create_text(
        WIDTH // 2,
        38,
        text="AUTONOMOUS NAVIGATION DASHBOARD",
        fill="white",
        font=("Arial", 24, "bold")
    )

    canvas.create_oval(1190, 30, 1205, 45, fill="#22c55e", outline="")
    canvas.create_text(
        1220,
        38,
        text="SYSTEM ACTIVE",
        fill="#bbf7d0",
        font=("Arial", 14, "bold"),
        anchor="w"
    )

    moving = speed_level != "STOP"

    # Main big car simulation
    draw_navigation_scene(moving, speed_level, color, status)

    # Left speed gauge
    draw_gauge(
        cx=135,
        cy=370,
        radius=120,
        value=speed,
        max_value=100,
        title="SPEED",
        unit="km/h",
        color=color
    )

    # Right ultrasonic gauge
    display_distance = 0 if distance is None else int(distance)

    draw_gauge(
        cx=1265,
        cy=370,
        radius=120,
        value=min(display_distance, 100),
        max_value=100,
        title="ULTRASONIC",
        unit="cm",
        color=color
    )

    canvas.create_text(
        1265,
        540,
        text=f"{display_distance} cm",
        fill=color,
        font=("Arial", 26, "bold")
    )

    # Small camera feed at top-right corner of main view
    draw_panel(930, 105, 1160, 315, "YOLO CAMERA")

    camera_img = cv2_to_tk(frame)

    if camera_img:
        canvas.create_image(
            1045,
            225,
            image=camera_img
        )

    # Bottom status cards
    draw_panel(30, 700, 340, 785, "CURRENT STATUS")
    canvas.create_text(60, 745, text=status,
                       fill=color, font=("Arial", 24, "bold"), anchor="w")
    canvas.create_text(60, 770, text=message,
                       fill="#cbd5e1", font=("Arial", 12), anchor="w")

    draw_panel(370, 700, 680, 785, "DETECTED OBJECT")
    canvas.create_text(400, 745, text=last_detected_object,
                       fill="white", font=("Arial", 18, "bold"), anchor="w")

    draw_panel(710, 700, 1020, 785, "CONTROL DECISION")
    canvas.create_text(740, 745, text=status,
                       fill=color, font=("Arial", 22, "bold"), anchor="w")

    draw_panel(1050, 700, 1360, 785, "MODE")
    canvas.create_text(1080, 745, text="AUTONOMOUS",
                       fill="#38bdf8", font=("Arial", 22, "bold"), anchor="w")


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

    status, color, message, speed, speed_level = get_status(
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
        speed,
        speed_level
    )

    root.after(200, update)


def on_close():
    picam2.stop()
    cv2.destroyAllWindows()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

update()
root.mainloop()