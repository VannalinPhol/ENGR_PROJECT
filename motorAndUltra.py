#for ultrasonic sensor


#VCC  → Pi Pin 2
#GND  → Pi Pin 9
#TRIG → Pi Pin 29
#ECHO → Pi Pin 31


from time import sleep, time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Motor pins
PWMA = 12
AIN1 = 16
AIN2 = 18
STBY = 22

# Ultrasonic pins
TRIG = 29
ECHO = 31

# Setup motor
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

# Setup ultrasonic
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

pwmFreq = 100
pwma = GPIO.PWM(PWMA, pwmFreq)
pwma.start(0)

def get_distance():
    GPIO.output(TRIG, GPIO.LOW)
    sleep(0.05)

    GPIO.output(TRIG, GPIO.HIGH)
    sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    start_time = time()
    timeout = start_time + 0.03

    while GPIO.input(ECHO) == 0:
        start_time = time()
        if start_time > timeout:
            return None

    stop_time = time()
    timeout = stop_time + 0.03

    while GPIO.input(ECHO) == 1:
        stop_time = time()
        if stop_time > timeout:
            return None

    elapsed = stop_time - start_time
    distance = (elapsed * 34300) / 2
    return distance

def motor_forward(speed):
    GPIO.output(STBY, GPIO.HIGH)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    pwma.ChangeDutyCycle(speed)

def motor_stop():
    pwma.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

try:
    while True:
        distance = get_distance()

        if distance is None:
            print("No distance reading")
            motor_stop()
            sleep(0.5)
            continue

        print(f"Distance: {distance:.1f} cm")

        if distance > 50:
            print("Far object → Fast speed")
            motor_forward(100)

        elif distance > 25:
            print("Medium distance → Medium speed")
            motor_forward(60)

        elif distance > 10:
            print("Close distance → Slow speed")
            motor_forward(30)

        else:
            print("Too close → Stop")
            motor_stop()

        sleep(0.2)

except KeyboardInterrupt:
    print("Stopped")

finally:
    motor_stop()
    GPIO.output(STBY, GPIO.LOW)
    pwma.stop()
    GPIO.cleanup()