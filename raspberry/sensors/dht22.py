import Adafruit_DHT
import json
import time


class DHT22(object):
    def __init__(self):
        self.sensor = Adafruit_DHT.DHT22
        # self.sensor_id = "DHT22"
        self.device_agent = "DHT"
        self.setPin()  # Take the information about the PIN connected to the DHT sensor from the file configuration.json

    def setPin(self):
        self.readConfigurationFile()
        for sensor in self.configuration["sensors"]:
            if sensor["device_agent"] == self.device_agent:
                self.pin = sensor["pins"]["data"]

    def readConfigurationFile(self):
        with open("device_connector/configuration.json", "r") as input_file:
            self.configuration = json.load(input_file)

    def getMeasurements(self):
        """
        Return the measurements from the DHT22 as a tuple
        """
        self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        return (round(self.humidity, 2), round(self.temperature, 2))

    def getMeasurementsDict(self):
        """
        Return the measurements from the DHT22 as a dictionary
        """
        self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        values_dict = {
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "timestamp" : round(time.time())
        }
        return values_dict
    
    def readData(self):
        """
        Return an event list SML
        """
        self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        timestamp = round(time.time())
        events = [
            {"n": "temperature", "t": timestamp, "v": round(self.temperature, 2)},
            {"n": "humidity", "t": timestamp, "v": round(self.humidity, 2)},
        ]
        
        return events
        
        
        



# if __name__ == "__main__":
#     dhtSensor = DHT22()  # Instanciate the object
#     while True:
#         values = (
#             dhtSensor.getMeasurementsDict()
#         )  # Call the method to obtain the values in a dict
#         print(values["temperature"])
#         time.sleep(2)
