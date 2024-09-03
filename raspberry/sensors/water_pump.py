import RPi.GPIO as GPIO
from log import Logs
import json

class WaterPump(object):
    """
    Class to simulate water pumps actuator.
    The methods are: 
    - switchOn
    - switchOff
    """
    def __init__(self, actuator_id):
        self.actuator_id = actuator_id
        self.device_agent = "WaterPumps"
        self.status = False # The default status of the pump is off. 
        self.setupLights()

        

    def readConfigurationFile(self):
        with open("device_connector/configuration.json", "r") as input_file:
            self.configuration = json.load(input_file)


    def setPin(self):
        self.readConfigurationFile()
        for actuator in self.configuration["actuators"]:
            if actuator['actuator_id'] == self.actuator_id:
                if actuator["device_agent"] == self.device_agent:
                    self.blue = actuator["pins"]["blue"]

    def setupLights(self):
        #Set warnings off (optional)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        #Set LED pins
        self.setPin()
        GPIO.setup(self.blue,GPIO.OUT)
                        
    def switchOn(self):
        """
        Switch on water pump
        """
        try:
            self.status = True
            GPIO.output(self.blue,GPIO.HIGH)
            Logs.log("WATER PUMP", f"Status set to ON")
        except:
            Logs.error('WATER PUMP', 'Error during switching ON')


            
    def switchOff(self):
        """
        Switch off water pump
        """
        try:
            self.status = False
            GPIO.output(self.blue,GPIO.LOW)
            Logs.log("WATER PUMP", f"Status set to OFF")
        except:
            Logs.error('WATER PUMP', 'Error during switching OFF')






# Example of implementation
# if __name__ == '__main__':
#     try:
#             waterpump = WaterPump()
#             print('Swtiching on')
#             waterpump.switchOn()
#             while (True):
#                 pass
#     except:
#         print("Switching off")
#         waterpump.switchOff()