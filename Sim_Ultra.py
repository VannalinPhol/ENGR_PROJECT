import tkinter as tk
import time
from time import sleep
from gpiozero import DistanceSensor

# =========================
# ULTRASONIC SENSOR SETUP
# =========================

TRIGGER_PIN = 5
ECHO_PIN = 6

MAX_RANGE_CM = 400
SAMPLE_SIZE = 5

STOP_DISTANCE = 15
SLOW_DISTANCE = 40

sensor = DistanceSensor(
    echo=ECHO_PIN,
    trigger=TRIGGER_PIN,
    max_distance=MAX_RANGE_CM / 100,
    queue_len=SAMPLE_SIZE,
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
# GUI SETUP
# =========================

WIDTH = 1400
HEIGHT = 800

root = tk.Tk()
root.title("Ultrasonic Sensor Autonomous Car Dashboard")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.configure(bg="#06111c")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#06111c", highlightthickness=0)
canvas.pack()

distance_history = []
road_offset = 0
side_offset = 0

stop_until = 0
last_distance = 100


def get_status(distance, forced_stop=False):
    if distance is None:
        return "#94a3b8", "ERROR", "Sensor error", "0 km/h"

    if forced_stop:
        return "#ff3b30", "STOP", "Waiting 3 seconds", "0 km/h"

    if distance < STOP_DISTANCE:
        return "#ff3b30", "STOP", "Object detected", "0 km/h"
    elif distance < SLOW_DISTANCE:
        return "#ffd60a", "SLOW", "Object nearby", "25 km/h"
    else:
        return "#30ff5a", "FAST", "Path clear", "60 km/h"


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
    canvas.create_text(WIDTH // 2, 35, text="ULTRASONIC SENSOR CONTROL",
                       fill="white", font=("Arial", 24, "bold"))

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


def draw_sensor_zone(distance, forced_stop):
    color, status, message, speed = get_status(distance, forced_stop)

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


def draw_ui(distance, forced_stop):
    color, status, message, speed = get_status(distance, forced_stop)

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

    draw_panel(1050, 80, 1380, 370, "DISTANCE OVER TIME")

    if len(distance_history) > 1:
        points = []
        for i, d in enumerate(distance_history[-40:]):
            x = 1080 + i * 7
            y = 330 - min(d, 100) * 2
            points.append((x, y))

        for i in range(len(points) - 1):
            canvas.create_line(points[i][0], points[i][1],
                               points[i + 1][0], points[i + 1][1],
                               fill="#30ff5a", width=3)

    draw_panel(1050, 400, 1380, 620, "SENSOR STATUS")

    rows = [
        ("Trigger", f"GPIO{TRIGGER_PIN}"),
        ("Echo", f"GPIO{ECHO_PIN}"),
        ("Stop", "< 15 cm"),
        ("Slow", "15 - 40 cm"),
        ("Fast", "> 40 cm")
    ]

    y = 450
    for name, value in rows:
        canvas.create_text(1080, y, text=name, fill="#cbd5e1",
                           font=("Arial", 12), anchor="w")
        canvas.create_text(1350, y, text=value, fill="white",
                           font=("Arial", 12), anchor="e")
        y += 35


def update():
    global stop_until, last_distance

    now = time.time()
    distance = get_distance()

    if distance is not None:
        last_distance = distance
    else:
        distance = last_distance

    if distance < STOP_DISTANCE and now >= stop_until:
        stop_until = now + 3

    forced_stop = now < stop_until

    if forced_stop:
        moving = False
        speed_level = "STOP"
    elif distance < SLOW_DISTANCE:
        moving = True
        speed_level = "SLOW"
    else:
        moving = True
        speed_level = "FAST"

    distance_history.append(distance)

    draw_environment(moving, speed_level)
    draw_sensor_zone(distance, forced_stop)
    draw_car()
    draw_ui(distance, forced_stop)

    canvas.create_oval(1220, 25, 1235, 40, fill="#30ff5a", outline="")
    canvas.create_text(1250, 33, text="SYSTEM ACTIVE",
                       fill="#bbf7d0", font=("Arial", 14, "bold"), anchor="w")

    root.after(500, update)


update()
root.mainloop()