import RPi.GPIO as GPIO
import time
import json
from log import Logs


class HCSR04(object):
    def __init__(self):
        self.device_agent = "HCSR04"
        self.iteractions = 10
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.setPins()
                
    def readConfigurationFile(self):
        with open("/home/pi/smart_IoT-Vertical-Farm/device_connector/configuration.json", "r") as input_file:
            self.configuration = json.load(input_file)

    def setPins(self):
        self.readConfigurationFile()
        for sensor in self.configuration["sensors"]:
            if sensor["device_agent"] == self.device_agent:
                self.pin_trig = sensor["pins"]["TRIG"]
                self.pin_echo = sensor["pins"]["ECHO"]
                self.max_time = sensor["max_delay"]


    def readData(self):
        measurements = []
        try:
            for i in range (self.iteractions):    # 10 iteractions
                GPIO.setup(self.pin_trig,GPIO.OUT)
                GPIO.setup(self.pin_echo,GPIO.IN)

                GPIO.output(self.pin_trig,False)
                time.sleep(0.01)
                GPIO.output(self.pin_trig,True)
                time.sleep(0.00001)
                GPIO.output(self.pin_trig,False)
                pulse_start = time.time()
                timeout = pulse_start + self.max_time
                while GPIO.input(self.pin_echo) == 0 and pulse_start < timeout:
                    pulse_start = time.time()

                pulse_end = time.time()
                timeout = pulse_end + self.max_time
                while GPIO.input(self.pin_echo) == 1 and pulse_end < timeout:
                    pulse_end = time.time()

                pulse_duration = pulse_end - pulse_start
                distance = pulse_duration * 17000
                distance = round(distance, 2)

                # print(distance)
                measurements.append(distance)
                time.sleep(0.2)
                
                
            # In measurements we have the values from the sensor.
            # Remove the min and the max and compute the average
            # measurements.remove(min(measurements, key=lambda x:float(x)))   # using min()/max() + float + lambda function
            measurements.remove(min(measurements))
            measurements.remove(max(measurements))
            Logs.log('ULTRASONIC', 'Reading data from the sensor')
            return sum(measurements)/len(measurements)
        except:
            GPIO.cleanup()
            Logs.error('ULTRASONIC', 'Error during read data')


        
# ultrasonic = HCSR04()
# print(ultrasonic.readData())