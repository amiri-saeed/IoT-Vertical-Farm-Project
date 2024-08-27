import time
from datetime import datetime
import requests
import random
import json
import logging
import threading

from pub import mqt_pub
from utils.service_manager import ServiceManager

import cherrypy
from rest.rest_serv import Server

logging.basicConfig(level=logging.INFO)
sm = ServiceManager()


# SHELF SPECIFIC "water_punp"


# THINGSPEAK_HOST = "THINGSPEAK_HOST"
# DEV_CONNECTOR_HOST = "DEVICE_CONNECTOR_HOST"
# TELEGRAM_HOST = "TELEGRAM_HOST"
# CATALOG_HOST = "CATALOG_HOST"


class SensorDataRetriever:
    def __init__(self):
        # for scope of this management we have two type of sensors values to consider
        # water to konw if the water tank in the room is empty or not
        # moisture to know if the corresponding shelf needs water to be injected into it or not
        self.sensors = ["water", "moisture"]
        self.data = dict()


    def fetch_sensor_data(self, room, tower, shelf):
        
        tower = int(tower[-1])
        shelf = int(shelf[-1])
        
        for sensor in self.sensors:

            # this one is shared in the room, one water tank in the room
            if sensor == "water":
                THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")
                url = f"{THINGSPEAK_HOST}/retrieve?room={room}&tower={tower}&shelf={shelf}&sensor={sensor}&last=1"
                response = requests.get(url)
                # print(response.json())
                if response.status_code == 200:
                    water = []
                    for feed in response.json()["feeds"]:
                        water.append(float(feed["value"]))
                        # print(water)
                    # we do the mean to counter any inconsistancy in the measuring
                    # the better way is to do the clustering on the values
                    # to exclude any inconsistancy caused by miss-measuring
                    if len(water) != 0:
                        mean_water = sum(water)/len(water)
                        self.data[sensor] = mean_water
                    else:
                        self.data[sensor] = 0.001

            # this is shelf specific, for each shelf we have a value for its moisture
            if sensor == "moisture":
                THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")
                url = f"{THINGSPEAK_HOST}/retrieve?room={room}&tower={tower}&shelf={shelf}&sensor={sensor}&last=2"
                response = requests.get(url)
                if response.status_code == 200:
                    moistures = []
                    for feed in response.json()["feeds"]:
                        moistures.append(float(feed["value"]))
                    if len(moistures) != 0:
                        mean_moisture = sum(moistures)/len(moistures)
                        self.data[sensor] = mean_moisture
                    else:
                        self.data[sensor] = 0.001

        return self.data



class CatalogIntegration:
    def fetch_plant_info(self):
        CATALOG_HOST = sm.service_base_url("catalog")
        url = f"{CATALOG_HOST}/all"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None



class Shelf:
    def __init__(self, shelf_id, plant_id, status, light, status_light, water_pump):
        self.shelf_id = shelf_id
        self.plant_id = plant_id
        self.status = status
        self.light = light
        self.status_light = status_light
        self.water_pump = water_pump


class OptimalValues:
    def __init__(self, low_soil_moisture, high_soil_moisture):
        self.low_soil_moisture = low_soil_moisture
        self.high_soil_moisture = high_soil_moisture



class Farm:
    def __init__(self, shelves, optimal_values_map):
        self.shelves = shelves
        self.optimal_values_map = optimal_values_map

    @classmethod
    def initialize_from_catalog(cls, catalog_data):
        shelves = []
        optimal_values_map = {}
        
        for shelf_data in catalog_data["shelves"]:
            if shelf_data["room_id"] == "R1":
                shelf_id = f"{shelf_data['tower_id']}-{shelf_data['shelf_id']}"
                plant_id = shelf_data["plant_id"]
                state = shelf_data.get("status", "Unknown")
                type_id = next(plant["type_id"] for plant in catalog_data["plants"] if plant["plant_id"]==plant_id)

                optimal_values_map[shelf_id] = OptimalValues(
                    low_soil_moisture=next(pn["low_soil_moisture"] for pn in catalog_data["plant_nutrients"] if pn["type_id"]==type_id and pn["state"]==state),
                    high_soil_moisture=next(pn["high_soil_moisture"] for pn in catalog_data["plant_nutrients"] if pn["type_id"]==type_id and pn["state"]==state)
                )

                shelves.append(Shelf(
                    shelf_id=shelf_id,
                    plant_id=plant_id,
                    status=shelf_data["status"],
                    light=shelf_data["light"],
                    status_light=shelf_data["status_light"],
                    water_pump=shelf_data["water_pump"]
                ))

                
        return cls(shelves, optimal_values_map), optimal_values_map


    

class DataProcessor:
    @staticmethod
    def process_sensor_data(farm, retriever, optimal_values_map):
        processed_data = []
        for shelf in farm.shelves:
            tower_id, shelf_id = shelf.shelf_id.split('-')
            sensor_data = retriever.fetch_sensor_data(room=1, tower=tower_id, shelf=shelf_id)
            if sensor_data:
                optimal_values = optimal_values_map[shelf.shelf_id]
                processed_data.append({
                    "shelf_id": shelf_id,
                    "tower_id": tower_id,
                    "low_soil_moisture": optimal_values.low_soil_moisture,
                    "high_soil_moisture": optimal_values.high_soil_moisture,
                    "water_sensor": float(sensor_data["water"]),
                    "moisture_sensor": float(sensor_data["moisture"]),
                })
            else:
                logging.info(f"Failed to retrieve sensor data for Tower {tower_id}, Shelf {shelf_id}")
        return processed_data



class Notifier:
    def notify_user(self, room_id, payload):
        TELEGRAM_HOST = sm.service_base_url("telegram_interface")
        room_id = room_id[1:]
        url = f"{TELEGRAM_HOST}/notify_user?room={room_id}"
        resp = requests.post(url, json=payload)
        logging.info(url)

    def set_catalog_water(self, room_id, tower_id, shelf_id, water_pump):
        CATALOG_HOST = sm.service_base_url("catalog")
        url_water = f"{CATALOG_HOST}/shelves/{room_id}/{tower_id}/{shelf_id}?water_pump={water_pump}"
        req_water = requests.post(url_water)
        logging.info(req_water.json())
        if req_water.status_code == 200:
            actuator = req_water.json()["actuator_id"]
        return actuator, water_pump

    def set_device_status(self, actuator, command):
        payload = {}
        DEV_CONNECTOR_HOST = sm.service_base_url("device_connector_n")
        url_devices = f"{DEV_CONNECTOR_HOST}"
        payload["actuator"] = actuator
        payload["command"] = command.lower()
        logging.info(payload)
        req = requests.post(url_devices, json=payload)

    def tasks(self, processed_data):
        
        # pp(processed_data)
        room_id = "R1" # or 1

        ## in case of implementation in Device Connector
        # topic = "pub/room1/tower1/shelf1"
        # mqt_pub.publish_to_topic(topic, processed_data)
        
        # since the water is shared in the room we can check for any of the values
        logging.info("start of room specific tasks...")
        water_sensor = round(processed_data[0]["water_sensor"], 2)
        logging.info(f"current water level in tank: {water_sensor}")
        if int(water_sensor) < 50:
            # check if the water tank is half empty then we should notify user to fill it
            message_to_user = f"Fill the water tank in your Farm {room_id}.\nCurrent water level is %{water_sensor}."
            self.notify_user(room_id, message_to_user)
            logging.info(message_to_user)



        for data in processed_data:
            logging.info("\nstart of shelf specific tasks...")
            shelf_id = data["shelf_id"]
            tower_id = data["tower_id"]
            low_soil_moisture = data["low_soil_moisture"]
            high_soil_moisture = data["high_soil_moisture"]
            moisture_sensor = round(data["moisture_sensor"], 2)
            

            logging.info(f"Tower {tower_id}, Shelf {shelf_id}:")
            condition = f"low moisture {low_soil_moisture} and high moisture {high_soil_moisture}, current moisture {moisture_sensor}"
            logging.info(condition)

            # to check for the shelf soil moisture
            # in case of below minimum optimal, we should activate the water_pump for that tower/shelf
            # activating for a short short time and repeating this procedure a couple of times should
            # lead to convergence to the optimal range if the sensors work properly
            if moisture_sensor < low_soil_moisture:
                water_pump = "ON"
            elif moisture_sensor > high_soil_moisture:
                water_pump = "OFF"
            # else:
            #     logging.info("in optimal range...")
            #     water_pump = "OFF"

            message_for_shelves = f"In Tower {tower_id}, Shelf {shelf_id}: Water Pump wnet {water_pump}\n\nDue to:\n{condition}"
            logging.info(message_for_shelves)
            self.notify_user(room_id, message_for_shelves)


            # this part sets the catalog water_pump and set the devices actuators for shelf water_pump (based on the moisture level)
            try:
                actuator, command = self.set_catalog_water(room_id, tower_id, shelf_id, water_pump)
                self.set_device_status(actuator, command)
            except Exception as e:
                logging.error(str(e))
            logging.info('\n')




class Serv:

    def _jsonify_error(self, status, message, traceback, version):
        response = cherrypy.response
        response.headers['Content-Type'] = 'application/json'
        return json.dumps({'status': 'Failure', 'status_details': {
            'message': status,
            'description': message
        }})


    def rest_serv(self, SERVICE_RNET, SERVICE_PORT):
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True,
                'error_page.default': self._jsonify_error,
            }
        }
        cherrypy.config.update({'server.socket_port': SERVICE_PORT, 'server.socket_host': SERVICE_RNET})
        cherrypy.tree.mount(Server(self), '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()


    def start_rest(self, SERVICE_RNET, SERVICE_PORT):
        threading.Thread(target=self.rest_serv, kwargs={'SERVICE_RNET': SERVICE_RNET, 'SERVICE_PORT': SERVICE_PORT}).start()