import cv2

# Open camera
camera = cv2.VideoCapture(0)

# Check if camera opened
if not camera.isOpened():
    print("Cannot open camera")
    exit()

print("Camera started")

while True:

    # Read frame
    ret, frame = camera.read()

    if not ret:
        print("Failed to grab frame")
        break

    # Show camera window
    cv2.imshow("Raspberry Pi Camera", frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
camera.release()
cv2.destroyAllWindows()