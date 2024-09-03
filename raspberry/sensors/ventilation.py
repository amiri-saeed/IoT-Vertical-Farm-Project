import RPi.GPIO as GPIO
import time
import json
import datetime
import sys
sys.path.insert(0,'/home/pi/smart_IoT-Vertical-Farm')       # Command to search on external folder the file MyMQTT
from log import Logs

class MotorController(object):
    def __init__(self):
        # Setup
        GPIO.setmode(GPIO.BCM)
        self.device_agent = "MOTOR3V"
        self.setPin()
        # self.Motor1A = 24 # IN1
        # self.Motor1B = 23 # IN2
        # self.Motor1E = 25 # EN1
        try:
            GPIO.setup(self.Motor1A, GPIO.OUT)
            GPIO.setup(self.Motor1B, GPIO.OUT)
            GPIO.setup(self.Motor1E, GPIO.OUT)
        except:
            Logs.error("VENTILATION", "Error during reading configuration file")
            
    def readConfigurationFile(self):
        with open("device_connector/configuration.json", "r") as input_file:
            self.configuration = json.load(input_file)
            
    def setPin(self):
        self.readConfigurationFile()
        for actuator in self.configuration["actuators"]:
            if actuator["device_agent"] == self.device_agent:
                self.Motor1A = actuator["pins"]["Motor1A"]    # IN1
                self.Motor1B = actuator["pins"]["Motor1B"]    # IN2
                self.Motor1E = actuator["pins"]["Motor1E"]    # EN1


    def switchOn(self, direction=1):
        """
        Switch on the motor. It takes as input the direction of the rotation.
        Default direction is set to clockwise.
        """
        try:
            if direction == -1: 
                # counterclockwise direction
                GPIO.output(self.Motor1A,GPIO.HIGH)
                GPIO.output(self.Motor1B,GPIO.LOW)
                GPIO.output(self.Motor1E,GPIO.HIGH)
                Logs.log("VENTILATION", f"Status set to ON (counterclockwise)")

            else:   
                # clockwise direction if not specified otherwise
                GPIO.output(self.Motor1A,GPIO.LOW)
                GPIO.output(self.Motor1B,GPIO.HIGH)
                GPIO.output(self.Motor1E,GPIO.HIGH)
                Logs.log("VENTILATION", f"Status set to ON (clockwise)")
        except:
            Logs.error('VENTILATION', 'Error during switching ON')


            
    
    def switchOff(self):
        """
        Stops the motor
        """
        try:
            GPIO.output(self.Motor1E,GPIO.LOW)
            Logs.log("VENTILATION", f"Status set to OFF")
        except:
            Logs.error('VENTILATION', 'Error during switching OFF')



    def cleanUp(self):
        """
        The cleanup method sets all the used gpios to be inputs and disables the internal pull-ups/downs for those gpios.
        """
        GPIO.cleanup()



# Example of implementation
# if __name__ == '__main__':
#     ventilation = MotorController()
#     ventilation.switchOn()
#     time.sleep(10)
#     ventilation.switchOff()
#     ventilation.switchOn(-1)
#     time.sleep(10)
#     ventilation.switchOff()
#     ventilation.cleanUp()