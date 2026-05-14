import cv2

# Open Raspberry Pi camera
camera = cv2.VideoCapture(0)

# Check if camera opened
if not camera.isOpened():
    print("Cannot open camera")
    exit()

print("Camera started!")

while True:

    # Read frame from camera
    ret, frame = camera.read()

    # If frame not captured
    if not ret:
        print("Failed to grab frame")
        break

    # Show camera window
    cv2.imshow("Raspberry Pi Camera", frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera
camera.release()

# Close all windows
cv2.destroyAllWindows()