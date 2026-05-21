# TB6612FNG Single Motor Speed Test
# Raspberry Pi BOARD pin mode

from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Pins
PWMA = 12
AIN2 = 18
AIN1 = 16
STBY = 22

# Setup pins
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

# PWM setup
pwmFreq = 100
pwma = GPIO.PWM(PWMA, pwmFreq)

# Start PWM at 0%
pwma.start(0)

try:
    # Enable driver
    GPIO.output(STBY, GPIO.HIGH)

    # -------------------------
    # FORWARD TEST
    # -------------------------
    print("Forward - 30% speed")

    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    pwma.ChangeDutyCycle(30)
    sleep(3)

    print("Forward - 60% speed")
    pwma.ChangeDutyCycle(60)
    sleep(3)

    print("Forward - 100% speed")
    pwma.ChangeDutyCycle(100)
    sleep(3)

    # -------------------------
    # STOP
    # -------------------------
    print("Stop")

    pwma.ChangeDutyCycle(0)

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

    sleep(2)

    # -------------------------
    # REVERSE TEST
    # -------------------------
    print("Reverse - 50% speed")

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)

    pwma.ChangeDutyCycle(50)
    sleep(3)

    print("Reverse - 100% speed")

    pwma.ChangeDutyCycle(100)
    sleep(3)

    # -------------------------
    # FINAL STOP
    # -------------------------
    print("Final Stop")

    pwma.ChangeDutyCycle(0)

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

    GPIO.output(STBY, GPIO.LOW)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    pwma.stop()

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

    GPIO.output(STBY, GPIO.LOW)

    GPIO.cleanup()