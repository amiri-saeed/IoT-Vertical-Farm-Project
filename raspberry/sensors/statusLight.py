import RPi.GPIO as GPIO
from log import Logs
import json

class StatusLight(object):
    def __init__(self, actuator_id):
        self.actuator_id = actuator_id
        self.device_agent = "StatusLight"
        self.setupLights()
        

    def readConfigurationFile(self):
        with open("device_connector/configuration.json", "r") as input_file:
            self.configuration = json.load(input_file)
            
            
    def setPin(self):
        self.readConfigurationFile()
        for actuator in self.configuration["actuators"]:
            if actuator['actuator_id'] == self.actuator_id:
                if actuator["device_agent"] == self.device_agent:
                    self.red = actuator["pins"]["red"]
                    self.yellow = actuator["pins"]["yellow"]
                    self.green = actuator["pins"]["green"]
                    
  
    def setupLights(self):
        #Set warnings off (optional)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        #Set LED pins
        self.setPin()
        GPIO.setup(self.red,GPIO.OUT)
        GPIO.setup(self.yellow,GPIO.OUT)
        GPIO.setup(self.green,GPIO.OUT)
            
    def switchOn(self, color):
        """
        Switch on the led
        """
        try: 
            if color.lower() == 'red':
                GPIO.output(self.red,GPIO.HIGH)
                GPIO.output(self.yellow,GPIO.LOW)
                GPIO.output(self.green,GPIO.LOW)
                Logs.log("STATUS LIGHT", f"Color set to RED")
            elif color.lower() == 'yellow':
                GPIO.output(self.red,GPIO.LOW)
                GPIO.output(self.yellow,GPIO.HIGH)
                GPIO.output(self.green,GPIO.LOW)
                Logs.log("STATUS LIGHT", f"Color set to YELLOW")
            elif color.lower() == 'green':
                GPIO.output(self.red,GPIO.LOW)
                GPIO.output(self.yellow,GPIO.LOW)
                GPIO.output(self.green,GPIO.HIGH)
                Logs.log("STATUS LIGHT", f"Color set to GREEN")
        except:
            Logs.error('STATUS LIGHT', 'Error during switching ON / change color')


            

    
    def switchOff(self):
        """
        Switch off the led
        """
        try:
            GPIO.output(self.red,GPIO.LOW)
            GPIO.output(self.yellow,GPIO.LOW)
            GPIO.output(self.green,GPIO.LOW)
            Logs.log("STATUS LIGHT", f"Status set to OFF")
        except:
            Logs.error('STATUS LIGHT', 'Error during switching OFF')


    def cleanUp(self):
        """
        The cleanup method sets all the used gpios to be inputs and disables the internal pull-ups/downs for those gpios.
        """
        GPIO.cleanup()



# # Example of implementation
# if __name__ == '__main__':
#     try:
#             statuslights = StatusLight()
#             print('Swtiching on')
#             statuslights.switchOn('red')
#             while (True):
#                 pass
#     except:
#         print("Cleaning up")
#         statuslights.cleanUp()