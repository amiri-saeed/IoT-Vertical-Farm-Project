import RPi.GPIO as GPIO
from log import Logs
import json

class UVLights(object):
    def __init__(self, actuator_id):
        self.actuator_id = actuator_id
        self.device_agent = "UVLights"
        self.setupLights()
        

    def readConfigurationFile(self):
        with open("device_connector/configuration.json", "r") as input_file:
            self.configuration = json.load(input_file)
            
            
    def setPin(self):
        self.readConfigurationFile()
        for actuator in self.configuration["actuators"]:
            if actuator['actuator_id'] == self.actuator_id:
                if actuator["device_agent"] == self.device_agent:
                    self.leds = actuator["pins"]["leds"]                    
  
    def setupLights(self):
        #Set warnings off (optional)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        #Set LED pins
        self.setPin()
        GPIO.setup(self.leds,GPIO.OUT)
            
    def switchOn(self):
        """
        Switch on the led
        """
        try:
            GPIO.output(self.leds,GPIO.HIGH)
            Logs.log("UV LIGHTS", f"Status set to ON")
        except:
            Logs.error('UV LIGHTS', 'Error during switching ON')

    
    def switchOff(self):
        """
        Switch off the led
        """
        try:
            GPIO.output(self.leds,GPIO.LOW)
            Logs.log("UV LIGHTS", f"Status set to OFF")
        except:
            Logs.error('UV LIGHTS', 'Error during switching OFF')



    def cleanUp(self):
        """
        The cleanup method sets all the used gpios to be inputs and disables the internal pull-ups/downs for those gpios.
        """
        GPIO.cleanup()


# led = UVLights('shelf_light_001')
# led.switchOn()