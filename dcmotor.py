from time import sleep
import RPi.GPIO as GPIO

# Use physical pin numbers
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Motor A pins
PWMA = 12
AIN1 = 16
AIN2 = 18

# Motor B pins
PWMB = 11
BIN1 = 15
BIN2 = 13

# Standby pin
STBY = 22

# PWM frequency
PWM_FREQ = 100

# Setup pins
motor_pins = [PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY]

for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# Setup PWM
pwma = GPIO.PWM(PWMA, PWM_FREQ)
pwmb = GPIO.PWM(PWMB, PWM_FREQ)

pwma.start(0)
pwmb.start(0)

def runMotor(motor, speed, direction):
    GPIO.output(STBY, GPIO.HIGH)

    if direction == 0:
        in1 = GPIO.HIGH
        in2 = GPIO.LOW
    else:
        in1 = GPIO.LOW
        in2 = GPIO.HIGH

    if motor == 0:
        GPIO.output(AIN1, in1)
        GPIO.output(AIN2, in2)
        pwma.ChangeDutyCycle(speed)

    elif motor == 1:
        GPIO.output(BIN1, in1)
        GPIO.output(BIN2, in2)
        pwmb.ChangeDutyCycle(speed)

def forward(speed):
    runMotor(0, speed, 0)
    runMotor(1, speed, 0)

def reverse(speed):
    runMotor(0, speed, 1)
    runMotor(1, speed, 1)

def turnLeft(speed):
    runMotor(0, speed, 1)
    runMotor(1, speed, 0)

def turnRight(speed):
    runMotor(0, speed, 0)
    runMotor(1, speed, 1)

def motorStop():
    pwma.ChangeDutyCycle(0)
    pwmb.ChangeDutyCycle(0)

    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    GPIO.output(STBY, GPIO.LOW)

try:
    while True:
        print("Forward")
        forward(60)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

        print("Reverse")
        reverse(60)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

        print("Turn Left")
        turnLeft(60)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

        print("Turn Right")
        turnRight(60)
        sleep(2)

        print("Stop")
        motorStop()
        sleep(1)

except KeyboardInterrupt:
    print("Program stopped by user")

finally:
    motorStop()
    pwma.stop()
    pwmb.stop()
    GPIO.cleanup()