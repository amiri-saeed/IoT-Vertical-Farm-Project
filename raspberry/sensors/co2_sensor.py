import random
import time
import datetime
import sys
# sys.path.insert(0,'D:\Polito\Magistrale\Programming for IOT\Project\smart_IoT-Vertical-Farm')       # Command to search on external folder the file MyMQTT
# from MyMQTT import MQTTConnector
from threading import Thread    # lib to use  multi threading


_sleep_time = 25


class SimulatedCO2Sensor(Thread):
    """
    Simulates a CO2 sensor with random fluctuations within a range.
    """

    def __init__(self, sensor_id ,baseline_co2, noise_range, final_path = 'sensors/co2_measurements', file_extension = '.csv'):
        Thread.__init__(self)   # init of thread
        self.baseline_co2 = baseline_co2
        self.noise_range = noise_range
        self.sensor_id = sensor_id
        self.file_extension = file_extension
        self.final_path = final_path
        self.sensor_on = True   # indicates that the sensor is on


    def readCO2(self):
        """
        Simulates a CO2 reading with random noise.
        """
        noise = random.uniform(-float(self.noise_range), float(self.noise_range))
        return (float(self.baseline_co2) + float(noise))
    
    def modifyBaselineCO2(self, new_baseline):
        self.baseline_co2 = new_baseline
        
        
    def writeFile(self):
        """
        Write the values in an output file. The path and the extension are defined during the instance of the object.
        """
        with open( self.final_path + '/' + self.sensor_id + self.file_extension, 'a') as output_file:
            # The output file should be a csv formatted in this way: ID; CO2 value; measurement unit; Timestamp;
            output_file.write(self.sensor_id + ";" + str(round(self.readCO2(),2)) + ";" + 'ppm' + ";" + str(round(time.time())) + '\n')


    def run(self):
        """
        Start the sensor
        """
        while (self.sensor_on): # if the sensor is switched on
            self.writeFile()
            time.sleep(_sleep_time)  # Cooldown



# if __name__ == "__main__":
#     # Example usage
#     sensor = SimulatedCO2Sensor('CO2_sensor1',400, 20)  # Baseline 400ppm, noise +-20ppm

#     for _ in range(5):
#         # co2_level = sensor.readCO2()
#         # print(f"CO2 level: {co2_level:.1f} ppm")
#         sensor.writeFile()
#         time.sleep(1)
    
#     topic = "orlando/iot/1"
#     # Publisher section
#     publisher = MQTTConnector("mypubtestpubIOT",'mqtt.eclipseprojects.io', 1883)
#     publisher.start()
#     a = 0
#     while (a < 10):
#         a += 1
#         publisher.myPublish(topic, str(a))
#         time.sleep(1)
#     # Disconnect the publisher
#     publisher.stop()
    
#     # Subscriber section
#     subscriber = MQTTConnector("mypubtestpubIOT",'mqtt.eclipseprojects.io', 1883)
#     subscriber.start()
#     subscriber.mySubscribe(topic)
#     # To stay connected:
#     while (True):
#         time.sleep(1)
#     # Disconnect the subscriber:
#     subscriber.stop()