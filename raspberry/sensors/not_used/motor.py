from time import sleep
from gpiozero import Motor, LED

motor = Motor(17,18)
motorSwitch = LED(27)

motorSpeedForward = 0
motorSpeedBackward = 0


def forwardSpeedIncrease():
    global motorSpeedForward
    motor.forward(speed=motorSpeedForward)
    print("Increased speed of motor backward. Current speed = "+ str(motorSpeedForward))
    motorSpeedForward += 0.1
    if motorSpeedForward >= 1:
        motorSpeedForward = 1

def forwardSpeedReduce():
    global motorSpeedForward
    motor.forward(speed=motorSpeedForward)
    print("Reduce speed of motor forward. Current speed = "+ str(motorSpeedForward))
    motorSpeedForward -= 0.1
    if motorSpeedForward <= 0:
        motorSpeedForward = 0

def backwardSpeedIncrease():
    global motorSpeedBackward
    motor.forward(speed=motorSpeedBackward)
    print("Increased speed of motor backward. Current speed = "+ str(motorSpeedBackward))
    motorSpeedBackward += 0.1
    if motorSpeedBackward >= 1:
        motorSpeedBackward = 1

def backwardSpeedReduce():
    global motorSpeedBackward
    motor.backward(speed=motorSpeedBackward)
    print("Reduce speed of motor backward. Current speed = "+ str(motorSpeedBackward))
    motorSpeedBackward -= 0.1
    if motorSpeedBackward <= 0:
        motorSpeedBackward = 0


if __name__ == '__main__':
    motorSwitch.on()
    motorSpeedForward = 10
    sleep(2)
    motorSwitch.off()
