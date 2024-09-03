import RPi.GPIO as GPIO
from time import sleep
#Set warnings off (optional)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#Set Button and LED pins
Button = 6
LED_RED = 16
LED_GREEN = 26

#Setup Button and LED
GPIO.setup(Button,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_RED,GPIO.OUT)
GPIO.setup(LED_GREEN,GPIO.OUT)
flag = 0

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
        