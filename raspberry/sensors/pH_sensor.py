import random
import time
import datetime
import sys
from threading import Thread    # lib to use  multi threading


_sleep_time = 25


class SimulatedpHSensor(Thread):
    """
    Simulates a pH sensor with random fluctuations within a range.
    """

    def __init__(self, sensor_id ,baseline_pH, noise_range, final_path = 'sensors/pH_measurements', file_extension = '.csv'):
        Thread.__init__(self)   # init of thread
        self.baseline_pH = baseline_pH
        self.noise_range = noise_range
        self.sensor_id = sensor_id
        self.file_extension = file_extension
        self.final_path = final_path
        self.sensor_on = True   # indicates that the sensor is on


    def readpH(self):
        """
        Simulates a pH reading with random noise.
        """
        noise = random.uniform(-float(self.noise_range), float(self.noise_range))
        return (float(self.baseline_pH) + float(noise))
    
    def modifyBaselinepH(self, new_baseline):
        self.baseline_pH = new_baseline
        
        
    def writeFile(self):
        """
        Write the values in an output file. The path and the extension are defined during the instance of the object.
        """
        with open( self.final_path + '/' + self.sensor_id + self.file_extension, 'a') as output_file:
            # The output file should be a csv formatted in this way: ID; CO2 value; measurement unit; Timestamp;
            output_file.write(self.sensor_id + ";" + str(round(self.readpH(),2)) + ";" + str(round(time.time())) + '\n')


    def run(self):
        """
        Start the sensor
        """
        while (self.sensor_on): # if the sensor is switched on
            self.writeFile()
            time.sleep(_sleep_time)  # Cooldown

