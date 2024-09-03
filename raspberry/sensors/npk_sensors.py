import json
import time
import datetime
import random
from threading import Thread    # lib to use  multi threading
import RPi.GPIO as GPIO
import sys
sys.path.insert(0,'/home/pi/smart_IoT-Vertical-Farm')
from log import Logs

_sleep_time = 25

class NPKSimulator (Thread):
    def __init__(self, sensor_id, ranges, refresh_rate = 30, final_path = 'sensors/npk_sensors_measurements', file_extension = '.csv'):
        Thread.__init__(self)   # init of thread
        self.sensor_id = sensor_id
        self.device_agent = "npk"
        self.ranges = ranges  # range is a dictionary formatted as  { "n" : "2-3", "p" : "0,5-1", "k" : "3-4" }
        self.refresh_rate = refresh_rate
        self.final_path = final_path
        self.file_extension = file_extension
        self.sensor_on = True   # indicates that the sensor is on
        self.nutrient_ok = True # If the nutrients should be generated as optimal values
        self.nutrient_low = False   # If the nutrients should be generated as values below threshold
        self.nutrient_high = False  # If the nutrients should be generated as values upper threshold
        self.nutrients_range = {}
        self.setupController()
        self.cleanOldFiles()
    
    def readConfigurationFile(self):
        with open("device_connector/configuration.json", "r") as input_file:
            self.configuration = json.load(input_file)
            
            
    def setPin(self):
        self.readConfigurationFile()
        for sensor in self.configuration["sensors"]:
            if sensor["device_agent"] == self.device_agent:
                self.Button = sensor["pins"]["button"]
                self.LED_RED = sensor["pins"]["RED"]
                self.LED_GREEN = sensor["pins"]["GREEN"]
            
    def setupController(self):
        #Set warnings off (optional)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        #Set Button and LED pins
        self.setPin()
        # self.Button = 6
        # self.LED_RED = 16
        # self.LED_GREEN = 26
        #Setup Button and LED
        GPIO.setup(self.Button,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_RED,GPIO.OUT)
        GPIO.setup(self.LED_GREEN,GPIO.OUT)
        self.flag = 0
        
    def computeRangesValue(self, ranges):
        for substance, range in ranges.items():
            range_split = range.split('-')
            range_min = float(range_split[0])
            range_max = float(range_split[1])
            self.nutrients_range[substance] = [range_min, range_max]
        Logs.log("NPK Sensors", f"The nutrients ranges are: {self.nutrients_range}")
        # print (self.nutrients_range)

        
    def generateOptimalValue(self, range_min, range_max):
        self.last_value = random.uniform(range_min, range_max)
        return round(self.last_value,2)
    
    def generateNonOptimalLowValue(self, range_min):
        self.last_value = random.uniform(0, range_min)
        return round(self.last_value, 2)
    
    def generateNonOptimalHighValue(self, range_max):
        self.last_value = random.uniform(range_max, range_max + 2)
        return round(self.last_value, 2)
    
    def checkButton(self):
        button_state = GPIO.input(self.Button)
        # print(button_state)

        if button_state==0:     # When we press the button we change the status of the nutrients!
            # sleep(0.5)
            if self.nutrient_ok==True:  # If the nutrient were ok, now they are not
                self.nutrient_ok = False
                if (self.nutrient_low == True): # The values out of range could be lower or higher, alternately
                    Logs.log("NPK Sensors", "Nutrients are set out of range (HIGHER)")
                    self.nutrient_low = False
                    self.nutrient_high = True
                else:
                    Logs.log("NPK Sensors", "Nutrients are set out of range (LOWER)")
                    self.nutrient_low = True
                    self.nutrient_high = False
            else:
                Logs.log("NPK Sensors", "Nutrients are set in range")
                self.nutrient_ok=True
        if self.nutrient_ok==False:
            GPIO.output(self.LED_RED,GPIO.HIGH)   # Red led ON (range out of value)
            GPIO.output(self.LED_GREEN,GPIO.LOW)  # Green led OFF (range out of value)
        else:
            GPIO.output(self.LED_RED,GPIO.LOW)       # Red led OFF (range in of value)
            GPIO.output(self.LED_GREEN,GPIO.HIGH)    # Green led ON (range in of value)
    
    
    def run(self):
        """
        Start the sensor. Compute the range and generates the values (in or out of optimal range).
        """
        self.computeRangesValue(self.ranges)
        while (self.sensor_on): # if the sensor is switched on
            value = {}
            self.checkButton()
            for nutrient in self.nutrients_range:
                # print(self.nutrients_range[nutrient])
                if self.nutrient_ok:
                    value[nutrient] = self.generateOptimalValue(self.nutrients_range[nutrient][0], self.nutrients_range[nutrient][1])
                elif (self.nutrient_low):
                    value[nutrient] = self.generateNonOptimalLowValue(self.nutrients_range[nutrient][0])
                elif (self.nutrient_high):
                    value[nutrient] = self.generateNonOptimalHighValue(self.nutrients_range[nutrient][1])
            self.writeFile(value)
            time.sleep(_sleep_time)  # Cooldown


    def writeFile(self, value):
        """
        Write the values in an output file. The path and the extension are defined during the instance of the object.
        """
        # try:   
        with open( self.final_path + '/' + self.sensor_id + self.file_extension, 'a') as output_file:
            # The output file should be a csv formatted in this way: ID; N; P; K;
            output_file.write(self.sensor_id + ";" + str(value['n']) + ";" + str(value['p']) + ";" + str(value['k'])+";" + str(round(time.time())) + '\n')
        # except:
        #     with open( self.final_path + '/' + self.sensor_id + self.file_extension, 'w') as output_file:
        #         # The output file should be a csv formatted in this way: ID; N; P; K;
        #         output_file.write(self.sensor_id + ";" + str(value['n']) + ";" + str(value['p']) + ";" + str(value['k'])+";" + str(round(time.time())) + '\n')
    
    def cleanOldFiles(self):
        """
        Delete all the files (with the correct file extension) in the destination folder
        """
        import os
        from glob import glob
        Logs.log("NPK SENSORS", f"Cleaning destination folder: {self.final_path}")
        files = glob(f'{self.final_path}/*{self.file_extension}')
        for f in files:
            os.remove(f)
        



# if __name__ == "__main__":
#     sensors = []
#     # with open('sensors/npk_sensors.json', 'r') as input_file:
#     #     input_sensors = json.load(input_file)
        
#     with open('device_connector/configuration.json', 'r') as input_file:
#         input_sensors = json.load(input_file)
    
    
#     for sensor in input_sensors['sensors']:
#         if sensor['device_agent'].lower() == 'npk':
#             sensors.append(NPKSimulator(sensor['sensor_id'], sensor['range']))
    
#     # print(sensors)  # list of all the object of the sensor class
#     try:
#         # print (sensors)
#         for elem in sensors:
#             elem.start()    # executes multithreading 
#     except KeyboardInterrupt:
#         GPIO.cleanup()
#         exit()