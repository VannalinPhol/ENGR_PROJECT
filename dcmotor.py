from gpiozero import Motor, PWMOutputDevice, DigitalOutputDevice
from time import sleep

# TB6612FNG pins using BCM GPIO numbers
AIN1 = 16   # Physical pin 36
AIN2 = 18   # Physical pin 12
PWMA = 12   # Physical pin 32
STBY = 25   # Physical pin 22

# Turn on motor driver
standby = DigitalOutputDevice(STBY)
standby.on()

# Direction pins
motor = Motor(forward=AIN1, backward=AIN2)

# Speed pin
pwm = PWMOutputDevice(PWMA)

try:
    print("Motor forward")
    pwm.value = 0.6
    motor.forward()
    sleep(3)

    print("Stop")
    motor.stop()
    sleep(1)

    print("Motor backward")
    pwm.value = 0.6
    motor.backward()
    sleep(3)

    print("Stop")
    motor.stop()
    pwm.off()

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    motor.stop()
    pwm.off()
    standby.off()