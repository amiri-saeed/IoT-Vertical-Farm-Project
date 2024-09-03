import json
import time
import cherrypy
from threading import Thread    # lib to use  multi threading
from DeviceAgentCSV import DeviceAgentCSV
import requests
import sys
from MyMQTT import MQTTConnector
# sys.path.insert(0,'D:\Polito\Magistrale\Programming for IOT\Project\smart_IoT-Vertical-Farm\sensors')       # Command to search on external folder the file MyMQTT
sys.path.insert(0,'/home/pi/smart_IoT-Vertical-Farm/sensors')       # Command to search on external folder the files
from dht22 import DHT22
from ultrasonic import HCSR04
from ventilation import MotorController
from npk_sensors import NPKSimulator
from statusLight import StatusLight
from uvLight import UVLights
from water_pump import WaterPump
from co2_sensor import SimulatedCO2Sensor
from pH_sensor import SimulatedpHSensor

sys.path.insert(0,'/home/pi/smart_IoT-Vertical-Farm')
from log import Logs
import RPi.GPIO as GPIO

_CATALOG_HOST = "10.241.8.146"
_CATALOG_PORT = "8080"

# class deviceConnector(Thread):
class deviceConnector(object):
    exposed = True
    def __init__(self):
        # Thread.__init__(self)
        self.cleanUp()
        # self.events_list = []
        self.readConfigurationFile()
        # self.device_id = 'rasp001'
        self.mqtt = MQTTConnector('RaspberryPi', 'mqtt.eclipseprojects.io', 1883)
        self.mqtt.start()


    def cleanUp(self):
        Logs.cleanLogs()    # Methods to clean all the log each new esecution of the device connector
        Logs.log("DEVICE CONNECTOR", "Cleaning the GPIOs")
        # GPIO.cleanup()
    
    def readConfigurationFile(self):
        """
        Read the configuration for all the sensors and save it into a dictionary
        NOTE: This method should be executed periodically.
        """
        try:
            with open('device_connector/configuration.json', 'r') as input_file:
                self.configuration = json.load(input_file)
                self.device_id = self.configuration['device_id']
                Logs.log('DEVICE CONNECTOR', 'Read configuration file')
            return self.configuration
        except:
            Logs.error('DEVICE CONNECTOR', 'Error during reading configuration file')

        
    def getTopic(self, sensor_id):
        """
        Method to retrieve the topic where to publish the data from the resource catalog.
        """
        # resource_catalog_endpoint = f'localhost:8080/topics?device_id={self.device_id}&sensor_id={sensor_id}'
        resource_catalog_endpoint = f'{_CATALOG_HOST}:{_CATALOG_PORT}/topics?device_id={self.device_id}&sensor_id={sensor_id}'
        topic_configuration = requests.get(resource_catalog_endpoint).json()    # Performs a GET request to the endpoint of the resource catalog
        return topic_configuration['topic_to_publish']
        
        # for element in self.configuration['sensors']:
        #     if element['sensor_id'] == sensor_id:
        #         topic_to_publish = 
        
        
    def postInfoResourceCatalog(self):
        """
        Method to post info about room, shelves, tower to the resource catalog.
        """
        import copy
        # url = self.configuration['post_resource_catalog']
        data_to_post = copy.deepcopy(self.configuration)    # Copy the configuration dictionary into data_to_post
        # del data_to_post['post_resource_catalog']    # remove the info about the resource catalog endpoint from the configuration
        url = data_to_post.pop('post_resource_catalog')    # remove the info about the resource catalog endpoint from the configuration
        properties_to_post = ['sensor_id', 'actuator_id', 'room_id', 'tower_id', 'shelf_id']   # List of the property we need to post to the resource catalog
        
        for sensor in data_to_post['sensors']:  # Loop through the sensors in the configuration
            for sensor_prop in sensor.copy():   # Loop through the properties in each sensor, .copy() is used to avoid changing the size of the dictionary during the iteration
                if not sensor_prop in properties_to_post:   # if the property is not present in the list of property we want to send, delete it
                    del sensor[sensor_prop]
        for actuator in data_to_post['actuators']:  # Loop through the sensors in the configuration
            for actuator_prop in actuator.copy():   # Loop through the properties in each sensor, .copy() is used to avoid changing the size of the dictionary during the iteration
                if not actuator_prop in properties_to_post:   # if the property is not present in the list of property we want to send, delete it
                    del actuator[actuator_prop]
        # print(data_to_post)
        
        # Set the Content-Type header to application/json
        headers = {'Content-Type': 'application/json'}

        # Send POST request with JSON data
        # Print the response
        try:
            Logs.log("DEVICE CONNECTOR", f"The POST request to the resource catalog has the following body: {json.dumps(data_to_post)}")
            response = requests.post(url, data=json.dumps(data_to_post), headers=headers)
            Logs.log("DEVICE CONNECTOR", f"The POST to the resource catalog has the following response body: {response.json()}")
            Logs.log("DEVICE CONNECTOR", f"The POST to the resource catalog got a result code: {response}")
        except: 
            Logs.error("DEVICE CONNECTOR", f"Error during POST request to resource catalog")


    # def parseSMLEvent(self, input_dict):
    #     output_dict = {'n':'','t':'','v':''}
    #     pass
    
    def sendData(self, end_point, sensor_id, event_list):
        """
        This methods is used to send the data via MQTT to Thingspeak connector. The format must be an SenML file:
        {
            "bn": "nome_dispositivo",
            "bt": 1646483600,
            "e": [
                {
                    "n": "temperatura_sensore_1",
                    "t": 1646483600,
                    "v": 22.5
                },
                {
                    "n": "temperatura_sensore_2",
                    "t": 1646483600,
                    "v": 23.1
                },
                {
                    "n": "temperatura_sensore_3",
                    "t": 1646483600,
                    "v": 21.9
                }
            ]
        }
        """
        output_SenML = {}   # output_SenML is a dict that contains the information to be sent to the Thingspeak connector, formatted in SenML.
        output_SenML['bn'] = sensor_id
        output_SenML['bt'] = round(time.time()) # Timestamp of when the output is created. It differs from the time in which the value is computed
        # output_SenML['e'] = self.events_list
        output_SenML['e'] = event_list
        Logs.log( "DEVICE CONNECTOR", f"Send data to {end_point} with payload: {json.dumps(output_SenML)}")
        self.mqtt.myPublish(end_point, output_SenML)
        # print(f"Send data to {end_point} with payload: {json.dumps(output_SenML)}")
        # print (json.dumps(output_SenML))
        
    def POST (self,*uri,**params):
        body=cherrypy.request.body.read()
        if len(body)>0:
            try:
                jsonBody=json.loads(body)
                for key in jsonBody.keys():
                    for actuator in self.configuration["actuators"]:
                        if jsonBody['actuator'] == actuator["actuator_id"]:
                            
                            if actuator["device_agent"] == 'MOTOR3V':
                                ventilation = MotorController()
                                if jsonBody['command'].lower() == 'on':
                                    Logs.log(f"DEVICE - CONNECTOR: {actuator['actuator_id']}", "Ventilation system switched ON")
                                    ventilation.switchOn()
                                    return "Executed"
                                    
                                if jsonBody['command'].lower() == 'off':
                                    Logs.log("DEVICE - CONNECTOR", "Ventilation system switched OFF")
                                    ventilation.switchOff()
                                    return "Executed"
                                return "Invalid command"
                            
                            elif actuator["device_agent"] == 'StatusLight':
                                available_color = ['red','yellow','green']
                                statusLight = StatusLight(actuator["actuator_id"])
                                chosen_color = jsonBody['command'].lower()
                                if chosen_color in available_color :    # the body of the post should contain the color to switch on
                                    statusLight.switchOn(chosen_color)
                                    Logs.log(f"DEVICE - CONNECTOR: {actuator['actuator_id']}", "Led are now {chosen_color}")
                                    return "Executed"
                                elif chosen_color == 'off':
                                    statusLight.switchOff()
                                    return "Executed"
                                else:
                                    Logs.error(f"DEVICE - CONNECTOR: {actuator['actuator_id']}", "Selected color ({chosen_color}) is not available")
                                    return "Invalid color"
                                
                            elif actuator["device_agent"] == 'UVLights':
                                uvLight = UVLights(actuator["actuator_id"])
                                if jsonBody['command'].lower() == 'on':
                                    Logs.log(f"DEVICE - CONNECTOR: {actuator['actuator_id']}", "UV lights switched ON")
                                    uvLight.switchOn()
                                    return "Executed"
                                    
                                if jsonBody['command'].lower() == 'off':
                                    Logs.log("DEVICE - CONNECTOR", "UV lights switched OFF")
                                    uvLight.switchOff()
                                    return "Executed"
                                return "Invalid command"
                            
                            elif actuator["device_agent"] == 'WaterPumps':
                                waterPump = WaterPump(actuator["actuator_id"])
                                if jsonBody['command'].lower() == 'on':
                                    Logs.log(f"DEVICE - CONNECTOR: {actuator['actuator_id']}", "Water pump switched ON")
                                    waterPump.switchOn()
                                    return "Executed"
                                if jsonBody['command'].lower() == 'off':
                                    Logs.log(f"DEVICE - CONNECTOR: {actuator['actuator_id']}", "Water pump switched OFF")
                                    waterPump.switchOff()
                                    return "Executed"
                                return "Invalid command"
                                                                                      
                    return "Actuator not found"
            except json.decoder.JSONDecodeError:
                Logs.error("CherryPy - POST", "CODE 400: Bad Request. Body must be a valid JSON")
                raise cherrypy.HTTPError(400,"Bad Request. Body must be a valid JSON")
            
            except:
                Logs.error("CherryPy - POST", "CODE 500: Internal Server Error")
                raise cherrypy.HTTPError(500,"Internal Server Error")
        else:
            Logs.error("CherryPy - POST", "CODE 400: Bad Request. Body is empty")
            raise cherrypy.HTTPError(400,"Bad Request. Body is empty")
        
    # def GET (self, *uri, **params):
    #     return "Get method..."
    


##################################
# Main section with threads
##################################

def cherryPyThread():
    ##################################
    # Cherry Py configuration section
    conf={
        '/':{
            'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on':True
        }
    }
    cherrypy.tree.mount(deviceConnector(),'/',conf)
    cherrypy.config.update({'server.socket_port':8080})
    cherrypy.config.update({'server.socket_host':'0.0.0.0'}) # in order to change the host
    cherrypy.engine.start()
    cherrypy.engine.block()
    ##################################


def startSimulatedSensors(raspberry):
    npk_sensors = []    # Array of NPK simulated sensors
    co2_sensors = []    # Array of CO2 simulated sensors
    pH_sensors = []    # Array of pH simulated sensors
    configuration = raspberry.readConfigurationFile()
    for sensor in configuration['sensors']:     # Loop through the sensor in the configuration file
        if sensor['device_agent'].lower() == 'npk':
            npk_sensors.append(NPKSimulator(sensor['sensor_id'], sensor['range']))
            try:
                for elem in npk_sensors:
                    elem.start()    # executes multithreading 
            except:
                Logs.error(f"DEVICE CONNECTOR: {sensor['sensor_id']}", "Error during simulation of NPK sensor")

        if sensor['device_agent'].lower() == 'co2':
            co2_sensors.append(SimulatedCO2Sensor(sensor['sensor_id'], sensor['range']['baseline'], sensor['range']['noise']))
            try:
                for elem in co2_sensors:
                    elem.start()
            except:
                Logs.error(f"DEVICE CONNECTOR: {sensor['sensor_id']}", "Error during simulation of CO2 sensor")
        
        if sensor['device_agent'].lower() == 'ph':
            pH_sensors.append(SimulatedpHSensor(sensor['sensor_id'], sensor['range']['baseline'], sensor['range']['noise']))
            try:
                for elem in pH_sensors:
                    elem.start()
            except:
                Logs.error(f"DEVICE CONNECTOR: {sensor['sensor_id']}", "Error during simulation of pH sensor")
        
                    
                    


def sensorsThread():
    raspberry = deviceConnector()
    startSimulatedSensors(raspberry)

    while True:
        # npk_sensors = []
        configuration = raspberry.readConfigurationFile()
        raspberry.postInfoResourceCatalog()
        for sensor in configuration['sensors']:     # Loop through the sensor in the configuration file
            # print(sensor['sensor_id'])         # Each sensor_id is here: sensor['sensor_id']
            if sensor['device_agent'].lower() == 'dht':
                ## Read the data from the DHT22
                dht = DHT22()
                raspberry.sendData(f"pub/{sensor['room_id']}/{sensor['tower_id']}/{sensor['shelf_id']}/{sensor['sensor_id']}", sensor['sensor_id'], dht.readData())
                
            if sensor['device_agent'].lower() == 'npk':
                Logs.log("DEVICE CONNECTOR", f"The sensor {sensor['sensor_id']} has a CSV Agent")
                # print(f"The sensor {sensor['sensor_id']} has a CSV Agent")
                npk = DeviceAgentCSV(sensor['variables'], sensor['sensor_id'], sensor['file_path'])   # Takes in input the variables to assign and the file to read
                
                data = npk.readData()
                npk_event_list = [
                    {
                        "n": "Nitrogen",
                        "t": data['Timestamp'],
                        "v": data['Nitrogen'],
                    },
                    {
                        "n": "Phosphorus",
                        "t": data['Timestamp'],
                        "v": data['Phosphorus'],
                    },
                    {
                        "n": "Potassium",
                        "t": data['Timestamp'],
                        "v": data['Potassium'],
                    }
                ]
                
                raspberry.sendData(f"pub/{sensor['room_id']}/{sensor['tower_id']}/{sensor['shelf_id']}/{sensor['sensor_id']}", sensor['sensor_id'], npk_event_list)
                # print(npk.readData())
                
            if sensor['device_agent'].lower() == 'hcsr04':
                ## Read the data from the HCSR04 Ultrasonic Sensor
                hcsr04 = HCSR04()
                height = hcsr04.readData()
                hcsr04_event_list = [
                    {
                        "n": "height",
                        "t": round(time.time()),
                        "v": height, 
                    }
                ]
                raspberry.sendData(f"pub/{sensor['room_id']}/{sensor['tower_id']}/{sensor['shelf_id']}/{sensor['sensor_id']}", sensor['sensor_id'], hcsr04_event_list)

            if sensor['device_agent'].lower() == 'co2':
                Logs.log("DEVICE CONNECTOR", f"The sensor {sensor['sensor_id']} has a CSV Agent")
                co2 = DeviceAgentCSV(sensor['variables'], sensor['sensor_id'], sensor['file_path'])   # Takes in input the variables to assign and the file to read
                data = co2.readData()
                co2_event_list = [
                    {
                        "n": "CO2 level",
                        "t": data['Timestamp'],
                        "v": data['CO2 level'],
                    }
                ]
                raspberry.sendData(f"pub/{sensor['room_id']}/{sensor['tower_id']}/{sensor['shelf_id']}/{sensor['sensor_id']}", sensor['sensor_id'], co2_event_list)

            if sensor['device_agent'].lower() == 'ph':
                Logs.log("DEVICE CONNECTOR", f"The sensor {sensor['sensor_id']} has a CSV Agent")
                pH = DeviceAgentCSV(sensor['variables'], sensor['sensor_id'], sensor['file_path'])   # Takes in input the variables to assign and the file to read
                data = pH.readData()
                pH_event_list = [
                    {
                        "n": "pH",
                        "t": data['Timestamp'],
                        "v": data['pH'],
                    }
                ]
                raspberry.sendData(f"pub/{sensor['room_id']}/{sensor['tower_id']}/{sensor['shelf_id']}/{sensor['sensor_id']}", sensor['sensor_id'], pH_event_list)

        time.sleep(30)
    
    


if __name__ == '__main__':
    # Create the threads
    cherryThread = Thread(target = cherryPyThread)
    mainThread = Thread(target = sensorsThread)
    
    # Start the threads
    cherryThread.start()
    mainThread.start()
    
    # Stop the execution of the current program until a thread is complete
    cherryThread.join()
    mainThread.join()
            
    # raspberry.getTopic()