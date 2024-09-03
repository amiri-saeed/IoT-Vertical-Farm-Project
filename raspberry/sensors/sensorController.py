import RPi.GPIO as GPIO
from time import sleep
#Set warnings off (optional)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class sensorController(object):
    def __init__(self, button, red, green):
        #Set Button and LED pins
        self.Button = button 
        self.LED_RED = red
        self.LED_GREEN = green

        #Setup Button and LED
        GPIO.setup(self.Button,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_RED,GPIO.OUT)
        GPIO.setup(self.LED_GREEN,GPIO.OUT)
        self.flag = 0

while True:
    button_state = GPIO.input(Button)
    print(button_state)

    if button_state==0:
        sleep(0.5)
        if flag==0:
            flag=1
        else:
            flag=0
    if flag==1:
        GPIO.output(LED_RED,GPIO.HIGH)   # Red led ON (range out of value)
        GPIO.output(LED_GREEN,GPIO.LOW)  # Green led OFF (range out of value)
    else:
        GPIO.output(LED_RED,GPIO.LOW)       # Red led OFF (range in of value)
        GPIO.output(LED_GREEN,GPIO.HIGH)    # Green led ON (range in of value)
        