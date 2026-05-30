import tkinter as tk
import time
from gpiozero import DistanceSensor
from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
from PIL import Image, ImageTk

# =========================
# ULTRASONIC SETUP
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
# CAMERA + YOLO SETUP
# =========================

model = YOLO("yolov8n.pt")

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
root.title("Ultrasonic + Camera Autonomous Car Dashboard")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.configure(bg="#06111c")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#06111c", highlightthickness=0)
canvas.pack()

road_offset = 0
side_offset = 0
distance_history = []

last_distance = 100
stop_until = 0
camera_image = None


# =========================
# LOGIC
# =========================

def get_status(distance, person_detected, forced_stop=False):
    if distance is None:
        return "#94a3b8", "ERROR", "Sensor error", "0 km/h", "STOP"

    if forced_stop:
        return "#ff3b30", "STOP", "Waiting 3 seconds", "0 km/h", "STOP"

    if person_detected and distance < STOP_DISTANCE:
        return "#ff3b30", "STOP", "Person close", "0 km/h", "STOP"

    if person_detected and distance < SLOW_DISTANCE:
        return "#ffd60a", "SLOW", "Person ahead", "25 km/h", "SLOW"

    if distance < STOP_DISTANCE:
        return "#ff3b30", "STOP", "Object close", "0 km/h", "STOP"

    if distance < SLOW_DISTANCE:
        return "#ffd60a", "SLOW", "Object nearby", "25 km/h", "SLOW"

    if person_detected:
        return "#30ff5a", "FAST", "Person far", "60 km/h", "FAST"

    return "#30ff5a", "FAST", "Path clear", "60 km/h", "FAST"


# =========================
# CAMERA DETECTION
# =========================

def detect_person():
    frame = picam2.capture_array()
    results = model(frame, verbose=False)

    person_detected = False

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # YOLO class 0 = person
            if class_id == 0 and confidence > 0.45:
                person_detected = True

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"person {confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

    return frame, person_detected


# =========================
# DRAWING FUNCTIONS
# =========================

def draw_panel(x1, y1, x2, y2, title):
    canvas.create_rectangle(x1, y1, x2, y2, fill="#071521", outline="#1e3a4f", width=2)
    canvas.create_text(x1 + 20, y1 + 25, text=title, fill="white",
                       font=("Arial", 13, "bold"), anchor="w")


def draw_tree(x, y, scale):
    canvas.create_rectangle(x - 8 * scale, y, x + 8 * scale, y + 70 * scale,
                            fill="#4b2e16", outline="")
    canvas.create_oval(x - 55 * scale, y - 55 * scale,
                       x + 55 * scale, y + 55 * scale,
                       fill="#14532d", outline="#22c55e")
    canvas.create_oval(x - 40 * scale, y - 95 * scale,
                       x + 40 * scale, y - 10 * scale,
                       fill="#166534", outline="")


def draw_light(x, y, scale):
    h = 110 * scale
    canvas.create_line(x, y, x, y - h, fill="#94a3b8", width=max(2, int(4 * scale)))
    canvas.create_line(x, y - h, x + 45 * scale, y - h - 15 * scale,
                       fill="#94a3b8", width=max(2, int(4 * scale)))
    canvas.create_oval(x + 35 * scale, y - h - 25 * scale,
                       x + 65 * scale, y - h + 5 * scale,
                       fill="#fde68a", outline="")


def draw_house(x, y, scale):
    w = 90 * scale
    h = 70 * scale

    canvas.create_rectangle(x - w / 2, y - h, x + w / 2, y,
                            fill="#475569", outline="#94a3b8")
    canvas.create_polygon(x - w / 2 - 10 * scale, y - h,
                          x, y - h - 45 * scale,
                          x + w / 2 + 10 * scale, y - h,
                          fill="#7f1d1d", outline="")
    canvas.create_rectangle(x - 35 * scale, y - 55 * scale,
                            x - 10 * scale, y - 35 * scale,
                            fill="#fde68a", outline="")


def draw_environment(moving, speed_level):
    global road_offset, side_offset

    canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#06111c", outline="")

    canvas.create_text(WIDTH // 2, 35, text="ULTRASONIC + CAMERA AUTONOMOUS CONTROL",
                       fill="white", font=("Arial", 22, "bold"))

    canvas.create_oval(360, 80, 1040, 520, fill="#0e2233", outline="")

    canvas.create_polygon(
        570, 130, 830, 130, 1120, 700, 280, 700,
        fill="#132433", outline="#dbeafe", width=3
    )

    for i in range(18):
        y = 150 + ((i * 45 + road_offset) % 560)
        scale = (y - 130) / 570
        left = 570 - 290 * scale
        right = 830 + 290 * scale
        canvas.create_line(left, y, right, y, fill="#1e4056", width=1)

    for i in range(10):
        y = 160 + ((i * 75 + road_offset) % 540)
        scale = (y - 130) / 570
        canvas.create_line(700, y, 700, y + 38 * scale,
                           fill="white", width=max(2, int(5 * scale)))

    for i in range(10):
        y = 130 + ((i * 95 + side_offset) % 620)
        scale = max(0.25, (y - 100) / 520)

        left_x = 520 - 360 * scale
        right_x = 880 + 360 * scale

        draw_tree(left_x, y, scale)
        draw_tree(right_x, y, scale)
        draw_light(left_x + 80 * scale, y, scale)
        draw_light(right_x - 80 * scale, y, scale)

        if i % 3 == 0:
            draw_house(left_x - 100 * scale, y + 30 * scale, scale)
            draw_house(right_x + 100 * scale, y + 30 * scale, scale)

    if moving:
        if speed_level == "FAST":
            road_offset += 20
            side_offset += 28
        elif speed_level == "SLOW":
            road_offset += 7
            side_offset += 10


def draw_sensor_zone(distance, color, status):
    canvas.create_polygon(
        620, 520, 780, 520, 740, 170, 660, 170,
        fill=color, stipple="gray25", outline=color, width=2
    )

    canvas.create_text(700, 250, text=status + " ZONE",
                       fill=color, font=("Arial", 20, "bold"))


def draw_car():
    cx = 700
    cy = 600

    canvas.create_oval(cx - 170, cy + 80, cx + 170, cy + 125,
                       fill="#020617", outline="")

    canvas.create_polygon(cx - 145, cy + 55, cx - 125, cy - 25,
                          cx - 70, cy - 95, cx + 70, cy - 95,
                          cx + 125, cy - 25, cx + 145, cy + 55,
                          cx + 105, cy + 95, cx - 105, cy + 95,
                          fill="#cbd5e1", outline="#f8fafc", width=2)

    canvas.create_polygon(cx - 70, cy - 78, cx + 70, cy - 78,
                          cx + 90, cy - 5, cx - 90, cy - 5,
                          fill="#020617", outline="#38bdf8", width=2)

    canvas.create_rectangle(cx - 120, cy + 42, cx + 120, cy + 52,
                            fill="#7f1d1d", outline="")
    canvas.create_oval(cx - 135, cy + 35, cx - 82, cy + 60,
                       fill="#ff1f1f", outline="")
    canvas.create_oval(cx + 82, cy + 35, cx + 135, cy + 60,
                       fill="#ff1f1f", outline="")


def draw_camera(frame):
    global camera_image

    draw_panel(1030, 80, 1380, 450, "CAMERA OBJECT DETECTION")

    frame = cv2.resize(frame, (320, 240))
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    image = Image.fromarray(frame)
    camera_image = ImageTk.PhotoImage(image)

    canvas.create_image(1205, 245, image=camera_image)


def draw_ui(distance, person_detected, color, status, message, speed):
    display_distance = "--" if distance is None else f"{distance:.1f}"

    draw_panel(30, 80, 390, 380, "ULTRASONIC SENSOR")

    canvas.create_text(260, 210, text=display_distance, fill="white",
                       font=("Arial", 48, "bold"))
    canvas.create_text(345, 218, text="cm", fill="white", font=("Arial", 16))

    canvas.create_text(70, 315, text="STATUS", fill="#cbd5e1",
                       font=("Arial", 12, "bold"), anchor="w")
    canvas.create_text(70, 350, text=status, fill=color,
                       font=("Arial", 24, "bold"), anchor="w")
    canvas.create_text(190, 350, text=message, fill=color,
                       font=("Arial", 13), anchor="w")

    draw_panel(1050, 480, 1380, 620, "SYSTEM STATUS")

    rows = [
        ("Trigger Pin", f"GPIO{TRIGGER_PIN}"),
        ("Echo Pin", f"GPIO{ECHO_PIN}"),
        ("Person Detected", "YES" if person_detected else "NO"),
        ("Stop Rule", "Person/Object < 15 cm"),
    ]

    y = 520
    for name, value in rows:
        canvas.create_text(1080, y, text=name, fill="#cbd5e1",
                           font=("Arial", 12), anchor="w")
        canvas.create_text(1350, y, text=value, fill="white",
                           font=("Arial", 12), anchor="e")
        y += 28

    cards = [
        ("CURRENT STATUS", status, message),
        ("DISTANCE", f"{display_distance} cm", "Ultrasonic Distance"),
        ("SPEED", speed, "Current Speed"),
        ("CAMERA", "PERSON" if person_detected else "CLEAR", "YOLO Detection")
    ]

    x = 30
    for title, main, sub in cards:
        canvas.create_rectangle(x, 650, x + 320, 780,
                                fill="#071521", outline="#1e3a4f", width=2)

        canvas.create_text(x + 20, 675, text=title,
                           fill="white", font=("Arial", 11), anchor="w")
        canvas.create_text(x + 20, 720, text=main,
                           fill=color, font=("Arial", 24, "bold"), anchor="w")
        canvas.create_text(x + 20, 755, text=sub,
                           fill="#cbd5e1", font=("Arial", 12), anchor="w")

        x += 340


# =========================
# MAIN UPDATE LOOP
# =========================

def update():
    global stop_until, last_distance

    now = time.time()

    distance = get_distance()

    if distance is not None:
        last_distance = distance
    else:
        distance = last_distance

    frame, person_detected = detect_person()

    if distance < STOP_DISTANCE and now >= stop_until:
        stop_until = now + 3

    forced_stop = now < stop_until

    color, status, message, speed, speed_level = get_status(
        distance,
        person_detected,
        forced_stop
    )

    moving = speed_level != "STOP"

    distance_history.append(distance)

    draw_environment(moving, speed_level)
    draw_sensor_zone(distance, color, status)
    draw_car()
    draw_camera(frame)
    draw_ui(distance, person_detected, color, status, message, speed)

    canvas.create_oval(1220, 25, 1235, 40, fill="#30ff5a", outline="")
    canvas.create_text(1250, 33, text="SYSTEM ACTIVE",
                       fill="#bbf7d0", font=("Arial", 14, "bold"), anchor="w")

    root.after(200, update)


def on_close():
    picam2.stop()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

update()
root.mainloop()