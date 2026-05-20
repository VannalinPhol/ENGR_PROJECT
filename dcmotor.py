# Test two DC motors wired together on AO1/AO2
# TB6612FNG + Raspberry Pi
# Using physical pin numbers

from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Motor A pins
PWMA = 12   # PWMA
AIN2 = 18   # AIN2
AIN1 = 16   # AIN1
STBY = 22   # STBY

# Setup
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

# PWM speed control
pwmA = GPIO.PWM(PWMA, 100)
pwmA.start(0)

try:
    print("Driver ON")
    GPIO.output(STBY, GPIO.HIGH)
    sleep(1)

    print("Forward")
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    pwmA.ChangeDutyCycle(100)
    sleep(5)

    print("Stop")
    pwmA.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    sleep(2)

    print("Reverse")
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    pwmA.ChangeDutyCycle(100)
    sleep(5)

    print("Stop")
    pwmA.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(STBY, GPIO.LOW)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    pwmA.ChangeDutyCycle(0)
    pwmA.stop()
    GPIO.cleanup()