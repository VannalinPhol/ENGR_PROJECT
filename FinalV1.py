import tkinter as tk
import time
import cv2
from gpiozero import DistanceSensor
from picamera2 import Picamera2
from ultralytics import YOLO

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

    last_detected_object = ", ".join(sorted(set(detected_names))) if detected_names else "None"

    return frame, person_detected


def cv2_to_tk(frame):
    frame = cv2.resize(frame, (700, 220))
    success, encoded = cv2.imencode(".ppm", frame)

    if not success:
        return None

    return tk.PhotoImage(data=encoded.tobytes())


def draw_panel(x1, y1, x2, y2, title):
    canvas.create_rectangle(x1, y1, x2, y2, fill="#071521", outline="#1e3a4f", width=2)
    canvas.create_text(
        x1 + 20,
        y1 + 25,
        text=title,
        fill="white",
        font=("Arial", 13, "bold"),
        anchor="w"
    )


def draw_gauge(cx, cy, radius, value, max_value, title, unit, color):
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                       outline="#1f2937", width=16)

    canvas.create_oval(cx - radius + 28, cy - radius + 28,
                       cx + radius - 28, cy + radius - 28,
                       outline="#111827", width=3)

    angle = int((value / max_value) * 270)

    canvas.create_arc(cx - radius + 10, cy - radius + 10,
                      cx + radius - 10, cy + radius - 10,
                      start=135, extent=-angle,
                      outline=color, width=12, style="arc")

    canvas.create_text(cx, cy - 30, text=str(value),
                       fill="white", font=("Arial", 50, "bold"))

    canvas.create_text(cx, cy + 25, text=unit,
                       fill="#9ca3af", font=("Arial", 18))

    canvas.create_text(cx, cy + 85, text=title,
                       fill=color, font=("Arial", 18, "bold"))


def draw_tree(x, y, scale):
    canvas.create_rectangle(x - 10 * scale, y, x + 10 * scale, y + 80 * scale,
                            fill="#4b2e16", outline="")

    canvas.create_oval(x - 65 * scale, y - 65 * scale,
                       x + 65 * scale, y + 65 * scale,
                       fill="#14532d", outline="#22c55e")

    canvas.create_oval(x - 45 * scale, y - 110 * scale,
                       x + 45 * scale, y - 20 * scale,
                       fill="#166534", outline="")


def draw_house(x, y, scale):
    w = 100 * scale
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


def draw_navigation_scene(moving, speed_level, color, status):
    global road_offset, side_offset

    draw_panel(270, 90, 1130, 500, "AUTONOMOUS NAVIGATION VIEW")

    # Background
    canvas.create_rectangle(285, 130, 1115, 490, fill="#0e2233", outline="")
    canvas.create_oval(360, 70, 1040, 520, fill="#10263a", outline="")

    # Road
    canvas.create_polygon(
        610, 150, 790, 150,
        1080, 490, 320, 490,
        fill="#132433",
        outline="#dbeafe",
        width=3
    )

    # Moving grid
    for i in range(14):
        y = 170 + ((i * 45 + road_offset) % 320)
        scale = (y - 150) / 340
        left = 610 - 290 * scale
        right = 790 + 290 * scale
        canvas.create_line(left, y, right, y, fill="#1e4056", width=1)

    # Road lane
    for i in range(8):
        y = 170 + ((i * 70 + road_offset) % 310)
        scale = (y - 150) / 340
        canvas.create_line(700, y, 700, y + 35 * scale,
                           fill="white", width=max(2, int(5 * scale)))

    # Side trees/houses
    for i in range(7):
        y = 155 + ((i * 80 + side_offset) % 340)
        scale = max(0.25, (y - 120) / 310)

        left_x = 580 - 330 * scale
        right_x = 820 + 330 * scale

        draw_tree(left_x, y, scale)
        draw_tree(right_x, y, scale)

        if i % 3 == 0:
            draw_house(left_x - 90 * scale, y + 40 * scale, scale)
            draw_house(right_x + 90 * scale, y + 40 * scale, scale)

    # Sensor zone
    canvas.create_polygon(
        610, 465,
        790, 465,
        745, 175,
        655, 175,
        fill=color,
        stipple="gray25",
        outline=color,
        width=2
    )

    canvas.create_text(700, 250, text=status + " ZONE",
                       fill=color, font=("Arial", 20, "bold"))

    # Big car
    draw_big_car(700, 420)

    if moving:
        if speed_level == "FAST":
            road_offset += 40
            side_offset += 50
        elif speed_level == "SLOW":
            road_offset += 12
            side_offset += 18


def draw_big_car(cx, cy):
    canvas.create_oval(cx - 230, cy + 80, cx + 230, cy + 140,
                       fill="#020617", outline="")

    canvas.create_polygon(
        cx - 210, cy + 65,
        cx - 170, cy - 70,
        cx - 90, cy - 155,
        cx + 90, cy - 155,
        cx + 170, cy - 70,
        cx + 210, cy + 65,
        cx + 150, cy + 120,
        cx - 150, cy + 120,
        fill="#cbd5e1",
        outline="#f8fafc",
        width=3
    )

    canvas.create_polygon(
        cx - 95, cy - 130,
        cx + 95, cy - 130,
        cx + 125, cy - 25,
        cx - 125, cy - 25,
        fill="#020617",
        outline="#38bdf8",
        width=3
    )

    canvas.create_polygon(
        cx - 140, cy - 15,
        cx + 140, cy - 15,
        cx + 105, cy + 55,
        cx - 105, cy + 55,
        fill="#111827",
        outline="#475569",
        width=2
    )

    canvas.create_rectangle(cx - 175, cy + 45, cx + 175, cy + 60,
                            fill="#7f1d1d", outline="")

    canvas.create_oval(cx - 205, cy + 35, cx - 120, cy + 75,
                       fill="#ff1f1f", outline="")

    canvas.create_oval(cx + 120, cy + 35, cx + 205, cy + 75,
                       fill="#ff1f1f", outline="")


def draw_dashboard(frame, distance, person_detected, status, color, message, speed, speed_level):
    global camera_img

    canvas.delete("all")

    # Header
    canvas.create_rectangle(0, 0, WIDTH, 75, fill="#070b10", outline="#111827")
    canvas.create_text(WIDTH // 2, 38, text="AUTONOMOUS NAVIGATION DASHBOARD",
                       fill="white", font=("Arial", 24, "bold"))

    canvas.create_oval(1190, 30, 1205, 45, fill="#22c55e", outline="")
    canvas.create_text(1220, 38, text="SYSTEM ACTIVE",
                       fill="#bbf7d0", font=("Arial", 14, "bold"), anchor="w")

    moving = speed_level != "STOP"

    # Main simulation
    draw_navigation_scene(moving, speed_level, color, status)

    # Left speed gauge
    draw_gauge(
        cx=145,
        cy=330,
        radius=125,
        value=speed,
        max_value=100,
        title="SPEED",
        unit="km/h",
        color=color
    )

    # Right ultrasonic gauge
    display_distance = 0 if distance is None else int(distance)

    draw_gauge(
        cx=1255,
        cy=330,
        radius=125,
        value=min(display_distance, 100),
        max_value=100,
        title="ULTRASONIC",
        unit="cm",
        color=color
    )

    canvas.create_text(1255, 500, text=f"{display_distance} cm",
                       fill=color, font=("Arial", 26, "bold"))

    # Smaller camera feed
    draw_panel(270, 520, 1130, 780, "YOLO CAMERA FEED")

    camera_img = cv2_to_tk(frame)

    if camera_img:
        canvas.create_image(700, 655, image=camera_img)

    # Bottom info on top of camera panel
    canvas.create_text(300, 755, text=f"Detected: {last_detected_object}",
                       fill="#30ff5a", font=("Arial", 13, "bold"), anchor="w")

    canvas.create_text(620, 755, text=f"Decision: {status}",
                       fill=color, font=("Arial", 13, "bold"), anchor="w")

    canvas.create_text(880, 755, text=f"Reason: {message}",
                       fill="#cbd5e1", font=("Arial", 13, "bold"), anchor="w")


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