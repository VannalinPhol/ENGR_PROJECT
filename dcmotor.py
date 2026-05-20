# DC Motor Control with TB6612FNG

from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# PWM frequency
pwmFreq = 100

# Setup pins for motor controller
GPIO.setup(12, GPIO.OUT)  # PWMA
GPIO.setup(18, GPIO.OUT)  # AIN2
GPIO.setup(16, GPIO.OUT)  # AIN1
GPIO.setup(22, GPIO.OUT)  # STBY
GPIO.setup(15, GPIO.OUT)  # BIN1
GPIO.setup(13, GPIO.OUT)  # BIN2
GPIO.setup(11, GPIO.OUT)  # PWMB

pwma = GPIO.PWM(12, pwmFreq)
pwmb = GPIO.PWM(11, pwmFreq)

pwma.start(0)
pwmb.start(0)

# Functions
def forward(spd):
    runMotor(0, spd, 0)
    runMotor(1, spd, 0)

def reverse(spd):
    runMotor(0, spd, 1)
    runMotor(1, spd, 1)

def turnLeft(spd):
    runMotor(0, spd, 0)
    runMotor(1, spd, 1)

def turnRight(spd):
    runMotor(0, spd, 1)
    runMotor(1, spd, 0)

def runMotor(motor, spd, direction):
    GPIO.output(22, GPIO.HIGH)  # turn on STBY

    in1 = GPIO.HIGH
    in2 = GPIO.LOW

    if direction == 1:
        in1 = GPIO.LOW
        in2 = GPIO.HIGH

    if motor == 0:
        GPIO.output(16, in1)   # AIN1
        GPIO.output(18, in2)   # AIN2
        pwma.ChangeDutyCycle(spd)

    elif motor == 1:
        GPIO.output(15, in1)   # BIN1
        GPIO.output(13, in2)   # BIN2
        pwmb.ChangeDutyCycle(spd)

def motorStop():
    pwma.ChangeDutyCycle(0)
    pwmb.ChangeDutyCycle(0)

    GPIO.output(16, GPIO.LOW)
    GPIO.output(18, GPIO.LOW)
    GPIO.output(15, GPIO.LOW)
    GPIO.output(13, GPIO.LOW)

    GPIO.output(22, GPIO.LOW)

# Main
try:
    while True:
        print("Forward")
        forward(50)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

        print("Reverse")
        reverse(50)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

        print("Turn Left")
        turnLeft(50)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

        print("Turn Right")
        turnRight(50)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

except KeyboardInterrupt:
    print("Stopped")

finally:
    motorStop()
    pwma.stop()
    pwmb.stop()
    GPIO.cleanup()