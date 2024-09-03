import random
import time
import datetime
import sys
from threading import Thread    # lib to use  multi threading


_sleep_time = 25


class SimulatedWaterLevelSensor(Thread):
    """
    Simulates a pH sensor with random fluctuations within a range.
    """

    def __init__(self, sensor_id ,baseline_water_level, noise_range, final_path = 'sensors/water_level_measurements', file_extension = '.csv'):
        Thread.__init__(self)   # init of thread
        self.baseline_water_level = baseline_water_level
        self.noise_range = noise_range
        self.sensor_id = sensor_id
        self.file_extension = file_extension
        self.final_path = final_path
        self.sensor_on = True   # indicates that the sensor is on


    def readWaterLevel(self):
        """
        Simulates a water level reading with random noise.
        """
        noise = random.uniform(-float(self.noise_range), float(self.noise_range))
        return (float(self.baseline_water_level) + float(noise))
    
    def modifyBaselinepH(self, new_baseline):
        self.baseline_water_level = new_baseline
        
        
    def writeFile(self):
        """
        Write the values in an output file. The path and the extension are defined during the instance of the object.
        """
        with open( self.final_path + '/' + self.sensor_id + self.file_extension, 'a') as output_file:
            # The output file should be a csv formatted in this way: ID; Water level; measurement unit; Timestamp;
            output_file.write(self.sensor_id + ";" + str(round(self.readWaterLevel(),2))+ "ml" + ";" + str(round(time.time())) + '\n')


    def run(self):
        """
        Start the sensor
        """
        while (self.sensor_on): # if the sensor is switched on
            self.writeFile()
            time.sleep(_sleep_time)  # Cooldown

