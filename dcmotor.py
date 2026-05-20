from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Pins from your reference image
PWMA = 12
AIN2 = 18
AIN1 = 16
STBY = 22

PWM_FREQ = 100

GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)

pwm = GPIO.PWM(PWMA, PWM_FREQ)
pwm.start(0)

try:
    print("Motor A forward")
    GPIO.output(STBY, GPIO.HIGH)

    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    pwm.ChangeDutyCycle(70)
    sleep(5)

    print("Stop")
    pwm.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(STBY, GPIO.LOW)

except KeyboardInterrupt:
    print("Stopped")

finally:
    pwm.stop()
    GPIO.cleanup()