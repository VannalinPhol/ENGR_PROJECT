import tkinter as tk
import time
import cv2
import math
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
root.configure(bg="#020711")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#020711", highlightthickness=0)
canvas.pack()

road_offset = 0
side_offset = 0
last_distance = 100
stop_until = 0
last_detected_object = "None"
camera_img = None


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
        return "SLOW", "#ffd60a", "Person nearby", 25, "SLOW"

    if distance < STOP_DISTANCE:
        return "STOP", "#ff3b30", "Object close", 0, "STOP"

    if distance < SLOW_DISTANCE:
        return "SLOW", "#ffd60a", "Object nearby", 25, "SLOW"

    return "FAST", "#30ff5a", "Path clear", 60, "FAST"


def detect_objects():
    global last_detected_object

    frame = picam2.capture_array()
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
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2
                )

    last_detected_object = ", ".join(sorted(set(detected_names))) if detected_names else "None"
    return frame, person_detected


def cv2_to_tk(frame):
    frame = cv2.resize(frame, (220, 160))
    success, encoded = cv2.imencode(".ppm", frame)

    if not success:
        return None

    return tk.PhotoImage(data=encoded.tobytes())


# =========================
# DRAWING HELPERS
# =========================

def draw_panel(x1, y1, x2, y2, title="", outline="#164e63", fill="#06111f"):
    canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=fill,
        outline=outline,
        width=2
    )

    if title:
        canvas.create_text(
            x1 + 18,
            y1 + 24,
            text=title,
            fill="#38bdf8",
            font=("Arial", 13, "bold"),
            anchor="w"
        )


def draw_header():
    canvas.create_rectangle(0, 0, WIDTH, 85, fill="#050910", outline="#0f172a")

    canvas.create_text(70, 42, text="18:40", fill="white", font=("Arial", 20, "bold"))
    canvas.create_text(155, 42, text="Melbourne · 24°C", fill="#94a3b8", font=("Arial", 12))

    canvas.create_text(
        WIDTH // 2,
        42,
        text="AUTONOMOUS NAVIGATION DASHBOARD",
        fill="white",
        font=("Arial", 24, "bold")
    )

    canvas.create_line(330, 42, 430, 42, fill="#38bdf8", width=2)
    canvas.create_line(430, 42, 450, 58, fill="#38bdf8", width=2)

    canvas.create_line(950, 58, 970, 42, fill="#38bdf8", width=2)
    canvas.create_line(970, 42, 1070, 42, fill="#38bdf8", width=2)

    canvas.create_oval(1210, 33, 1225, 48, fill="#22c55e", outline="")
    canvas.create_text(
        1245,
        41,
        text="SYSTEM ACTIVE",
        fill="#86efac",
        font=("Arial", 15, "bold"),
        anchor="w"
    )


def draw_vertical_gauge(cx, cy, rx, ry, value, max_value, title, unit, color, subtitle):
    canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, outline="#123456", width=3)
    canvas.create_oval(cx - rx + 10, cy - ry + 10, cx + rx - 10, cy + ry - 10,
                       outline="#1e293b", width=10)

    percentage = max(0, min(value / max_value, 1))

    canvas.create_arc(
        cx - rx + 35,
        cy - ry + 95,
        cx + rx - 35,
        cy + ry - 95,
        start=145,
        extent=-260,
        outline="#334155",
        width=3,
        style="arc"
    )

    canvas.create_arc(
        cx - rx + 35,
        cy - ry + 95,
        cx + rx - 35,
        cy + ry - 95,
        start=145,
        extent=-260 * percentage,
        outline=color,
        width=10,
        style="arc"
    )

    for i in range(11):
        angle = math.radians(145 - (260 * i / 10))
        x1 = cx + (rx - 70) * math.cos(angle)
        y1 = cy - 20 - (ry - 130) * math.sin(angle)
        x2 = cx + (rx - 55) * math.cos(angle)
        y2 = cy - 20 - (ry - 115) * math.sin(angle)
        canvas.create_line(x1, y1, x2, y2, fill="#64748b", width=1)

    canvas.create_text(cx, cy - 15, text=str(value), fill="white", font=("Arial", 54, "bold"))
    canvas.create_text(cx, cy + 55, text=unit, fill="#cbd5e1", font=("Arial", 17))

    canvas.create_rectangle(cx - 44, cy + 92, cx + 44, cy + 122,
                            outline=color, fill="#0a1724", width=1)
    canvas.create_text(cx, cy + 107, text=subtitle, fill=color, font=("Arial", 13, "bold"))

    canvas.create_text(cx, cy + 170, text=title, fill="#38bdf8",
                       font=("Arial", 13, "bold"))


def draw_tree(x, y, scale):
    canvas.create_rectangle(
        x - 7 * scale,
        y,
        x + 7 * scale,
        y + 55 * scale,
        fill="#4b2e16",
        outline=""
    )

    canvas.create_oval(
        x - 33 * scale,
        y - 32 * scale,
        x + 33 * scale,
        y + 32 * scale,
        fill="#0f5132",
        outline=""
    )

    canvas.create_oval(
        x - 24 * scale,
        y - 58 * scale,
        x + 24 * scale,
        y - 10 * scale,
        fill="#166534",
        outline=""
    )


def draw_house(x, y, scale):
    w = 60 * scale
    h = 45 * scale

    canvas.create_rectangle(
        x - w / 2,
        y - h,
        x + w / 2,
        y,
        fill="#475569",
        outline="#64748b"
    )

    canvas.create_polygon(
        x - w / 2 - 6 * scale,
        y - h,
        x,
        y - h - 28 * scale,
        x + w / 2 + 6 * scale,
        y - h,
        fill="#7f1d1d",
        outline=""
    )

    canvas.create_rectangle(
        x - 18 * scale,
        y - 32 * scale,
        x - 5 * scale,
        y - 20 * scale,
        fill="#fde68a",
        outline=""
    )


def draw_navigation_view(moving, speed_level, color, status):
    global road_offset, side_offset

    # Main centre panel
    draw_panel(320, 115, 1080, 705, "AUTONOMOUS NAVIGATION")

    canvas.create_rectangle(340, 155, 1060, 685, fill="#061827", outline="")
    canvas.create_rectangle(340, 155, 1060, 240, fill="#07111d", outline="")

    # Stars
    for x, y in [(380, 175), (520, 185), (640, 168), (810, 178), (970, 170), (880, 160)]:
        canvas.create_oval(x, y, x + 2, y + 2, fill="#64748b", outline="")

    # Mountains
    canvas.create_polygon(340, 240, 410, 205, 480, 235, 540, 210, 640, 240,
                          fill="#0f172a", outline="")
    canvas.create_polygon(830, 240, 930, 210, 1010, 230, 1060, 205, 1060, 240,
                          fill="#0f172a", outline="")

    # Ground grid
    for i in range(20):
        y = 240 + i * 22
        canvas.create_line(340, y, 1060, y, fill="#073047", width=1)

    for i in range(16):
        x = 340 + i * 50
        canvas.create_line(x, 240, 700, 685, fill="#073047", width=1)

    # Road
    canvas.create_polygon(
        630, 240,
        770, 240,
        1060, 685,
        340, 685,
        fill="#102132",
        outline="#38bdf8",
        width=2
    )

    canvas.create_line(630, 240, 340, 685, fill="#93c5fd", width=3)
    canvas.create_line(770, 240, 1060, 685, fill="#93c5fd", width=3)

    # Moving road lines
    for i in range(18):
        y = 255 + ((i * 45 + road_offset) % 420)
        scale = (y - 240) / 445
        left = 630 - 290 * scale
        right = 770 + 290 * scale
        canvas.create_line(left, y, right, y, fill="#164e63", width=1)

    # Centre lane
    for i in range(12):
        y = 255 + ((i * 65 + road_offset) % 410)
        scale = (y - 240) / 445
        canvas.create_line(700, y, 700, y + 35 * scale,
                           fill="#e0f2fe", width=max(2, int(4 * scale)))

    # Smaller side trees/houses - kept away from bottom text
    for i in range(7):
        y = 265 + ((i * 85 + side_offset) % 360)
        scale = max(0.18, (y - 230) / 430)

        left_x = 605 - 260 * scale
        right_x = 795 + 260 * scale

        if y < 620:
            draw_tree(left_x, y, scale)
            draw_tree(right_x, y, scale)

        if i % 3 == 0 and y < 600:
            draw_house(left_x - 55 * scale, y + 20 * scale, scale)
            draw_house(right_x + 55 * scale, y + 20 * scale, scale)

    # Sensor zone
    canvas.create_polygon(620, 550, 780, 550, 745, 300, 655, 300,
                          fill="#22c55e", stipple="gray50", outline="#22c55e", width=1)

    canvas.create_polygon(640, 405, 760, 405, 735, 285, 665, 285,
                          fill="#f59e0b", stipple="gray50", outline="#f59e0b", width=1)

    canvas.create_polygon(660, 335, 740, 335, 725, 255, 675, 255,
                          fill="#ef4444", stipple="gray50", outline="#ef4444", width=1)

    canvas.create_text(700, 355, text=status + " ZONE",
                       fill=color, font=("Arial", 18, "bold"))

    draw_car(700, 590)

    if moving:
        if speed_level == "FAST":
            road_offset += 35
            side_offset += 48
        elif speed_level == "SLOW":
            road_offset += 12
            side_offset += 18


def draw_car(cx, cy):
    canvas.create_oval(cx - 175, cy + 65, cx + 175, cy + 112, fill="#020617", outline="")

    canvas.create_polygon(
        cx - 145, cy + 40,
        cx - 120, cy - 55,
        cx - 70, cy - 115,
        cx + 70, cy - 115,
        cx + 120, cy - 55,
        cx + 145, cy + 40,
        cx + 110, cy + 85,
        cx - 110, cy + 85,
        fill="#e5e7eb",
        outline="#f8fafc",
        width=2
    )

    canvas.create_polygon(
        cx - 70, cy - 95,
        cx + 70, cy - 95,
        cx + 95, cy - 15,
        cx - 95, cy - 15,
        fill="#020617",
        outline="#38bdf8",
        width=2
    )

    canvas.create_polygon(
        cx - 110, cy + 0,
        cx + 110, cy + 0,
        cx + 85, cy + 48,
        cx - 85, cy + 48,
        fill="#111827",
        outline="#334155",
        width=2
    )

    canvas.create_rectangle(cx - 130, cy + 46, cx + 130, cy + 57,
                            fill="#7f1d1d", outline="")
    canvas.create_rectangle(cx - 135, cy + 42, cx - 65, cy + 58,
                            fill="#ef4444", outline="")
    canvas.create_rectangle(cx + 65, cy + 42, cx + 135, cy + 58,
                            fill="#ef4444", outline="")


def draw_camera_feed(frame):
    global camera_img

    # Camera panel with bright color border
    canvas.create_rectangle(875, 130, 1070, 325, fill="#020711", outline="#38bdf8", width=3)
    canvas.create_rectangle(881, 136, 1064, 319, fill="#06111f", outline="#f472b6", width=2)

    canvas.create_text(895, 154, text="YOLO CAMERA", fill="#38bdf8",
                       font=("Arial", 10, "bold"), anchor="w")
    canvas.create_text(1055, 154, text="● LIVE", fill="#ef4444",
                       font=("Arial", 10, "bold"), anchor="e")

    camera_img = cv2_to_tk(frame)

    if camera_img:
        canvas.create_image(972, 235, image=camera_img)


def draw_bottom_status(status, color, message):
    # Put this on top layer after all trees/car
    canvas.create_rectangle(360, 640, 1040, 700, fill="#020711", outline="#38bdf8", width=2)

    canvas.create_text(400, 670, text="◎", fill="#86efac", font=("Arial", 28, "bold"))
    canvas.create_text(445, 660, text="DETECTED OBJECT", fill="#cbd5e1",
                       font=("Arial", 10, "bold"), anchor="w")
    canvas.create_text(445, 684, text=last_detected_object, fill="#86efac",
                       font=("Arial", 13, "bold"), anchor="w")

    canvas.create_line(585, 650, 585, 690, fill="#1e293b")

    canvas.create_text(630, 670, text="⬟", fill="#f59e0b", font=("Arial", 26, "bold"))
    canvas.create_text(675, 660, text="DECISION", fill="#cbd5e1",
                       font=("Arial", 10, "bold"), anchor="w")
    canvas.create_text(675, 684, text=status, fill=color,
                       font=("Arial", 13, "bold"), anchor="w")

    canvas.create_line(805, 650, 805, 690, fill="#1e293b")

    canvas.create_text(850, 670, text="⌘", fill="#38bdf8", font=("Arial", 26, "bold"))
    canvas.create_text(895, 660, text="STATUS", fill="#cbd5e1",
                       font=("Arial", 10, "bold"), anchor="w")
    canvas.create_text(895, 684, text=message, fill="#38bdf8",
                       font=("Arial", 13, "bold"), anchor="w")


def draw_dashboard(frame, distance, person_detected, status, color, message, speed, speed_level):
    canvas.delete("all")

    draw_header()

    moving = speed_level != "STOP"

    # Left speed panel
    canvas.create_rectangle(35, 125, 295, 725, fill="#06111f", outline="#164e63", width=2)
    canvas.create_text(165, 175, text="SPEED", fill="#e5e7eb", font=("Arial", 14, "bold"))

    speed_label = "FAST" if speed == 60 else "SLOW" if speed == 25 else "STOP"

    draw_vertical_gauge(
        cx=165,
        cy=390,
        rx=95,
        ry=175,
        value=speed,
        max_value=100,
        title="DRIVE MODE",
        unit="km/h",
        color=color,
        subtitle=speed_label
    )

    canvas.create_text(165, 675, text="AUTONOMOUS", fill="#38bdf8",
                       font=("Arial", 13, "bold"))

    # Centre
    draw_navigation_view(moving, speed_level, color, status)

    # Camera with colored frame
    draw_camera_feed(frame)

    # Bottom readable status
    draw_bottom_status(status, color, message)

    # Right distance panel
    canvas.create_rectangle(1105, 125, 1365, 725, fill="#06111f", outline="#164e63", width=2)
    canvas.create_text(1235, 175, text="DISTANCE", fill="#e5e7eb", font=("Arial", 14, "bold"))

    display_distance = 0 if distance is None else int(distance)
    distance_label = "SAFE" if display_distance >= SLOW_DISTANCE else "SLOW" if display_distance >= STOP_DISTANCE else "STOP"

    draw_vertical_gauge(
        cx=1235,
        cy=390,
        rx=95,
        ry=175,
        value=min(display_distance, 400),
        max_value=400,
        title="ULTRASONIC",
        unit="cm",
        color=color,
        subtitle=distance_label
    )

    canvas.create_text(1235, 650, text="ULTRASONIC SENSOR",
                       fill="#cbd5e1", font=("Arial", 12, "bold"))
    canvas.create_text(1235, 680, text=f"{display_distance} cm",
                       fill=color, font=("Arial", 18, "bold"))


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