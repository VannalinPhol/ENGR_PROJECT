from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

PWMA = 12
AIN1 = 16
AIN2 = 18
STBY = 22

GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

pwm = GPIO.PWM(PWMA, 100)
pwm.start(0)

try:
    GPIO.output(STBY, GPIO.HIGH)

    print("Two motors forward together")
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    pwm.ChangeDutyCycle(80)
    sleep(5)

    print("Stop")
    pwm.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(STBY, GPIO.LOW)

finally:
    pwm.stop()
    GPIO.cleanup()