# TB6612FNG Dual Motor Test
# Raspberry Pi BOARD pin mode

from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Motor A pins
PWMA = 12
AIN2 = 18
AIN1 = 16

# Motor B pins
PWMB = 11
BIN1 = 15
BIN2 = 13

# Standby
STBY = 22

# Setup pins
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)

GPIO.setup(PWMB, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)

GPIO.setup(STBY, GPIO.OUT)

# PWM
pwmFreq = 100

pwma = GPIO.PWM(PWMA, pwmFreq)
pwmb = GPIO.PWM(PWMB, pwmFreq)

pwma.start(100)
pwmb.start(100)

try:
    # Enable driver
    GPIO.output(STBY, GPIO.HIGH)

    # -----------------------
    # FORWARD
    # -----------------------
    print("Both motors forward")

    # Motor A forward
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    # Motor B forward
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)

    sleep(5)

    # -----------------------
    # STOP
    # -----------------------
    print("Stop")

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    sleep(2)

    # -----------------------
    # REVERSE
    # -----------------------
    print("Both motors reverse")

    # Motor A reverse
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)

    # Motor B reverse
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)

    sleep(5)

    # -----------------------
    # STOP
    # -----------------------
    print("Stop")

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    GPIO.output(STBY, GPIO.LOW)

except KeyboardInterrupt:
    print("Stopped")

finally:
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    GPIO.output(STBY, GPIO.LOW)

    pwma.stop()
    pwmb.stop()

    GPIO.cleanup()