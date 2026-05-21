# TB6612FNG Motor Test
# Raspberry Pi GPIO BOARD mode

from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# PWM Frequency
pwmFreq = 100

# Motor controller pins
PWMA = 12
AIN2 = 18
AIN1 = 16
STBY = 22
BIN1 = 15
BIN2 = 13
PWMB = 11

# Setup pins
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)

# Setup PWM
pwma = GPIO.PWM(PWMA, pwmFreq)
pwmb = GPIO.PWM(PWMB, pwmFreq)

pwma.start(0)
pwmb.start(0)

# -----------------------------
# Motor Functions
# -----------------------------

def motorA_forward(speed):
    print("Motor A Forward")

    GPIO.output(STBY, GPIO.HIGH)

    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    pwma.ChangeDutyCycle(speed)

def motorA_reverse(speed):
    print("Motor A Reverse")

    GPIO.output(STBY, GPIO.HIGH)

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)

    pwma.ChangeDutyCycle(speed)

def stopMotor():
    print("Stop")

    pwma.ChangeDutyCycle(0)
    pwmb.ChangeDutyCycle(0)

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    GPIO.output(STBY, GPIO.LOW)

# -----------------------------
# Main Program
# -----------------------------

try:

    # Forward
    motorA_forward(100)
    sleep(5)

    stopMotor()
    sleep(2)

    # Reverse
    motorA_reverse(100)
    sleep(5)

    stopMotor()

except KeyboardInterrupt:
    print("Program stopped")

finally:
    stopMotor()

    pwma.stop()
    pwmb.stop()

    GPIO.cleanup()