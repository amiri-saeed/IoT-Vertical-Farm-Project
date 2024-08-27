import time
import datetime
import requests
import random
import statistics
import logging
import threading
from collections import defaultdict
import json
from pprint import pprint as pp

from pub import mqt_pub
from utils.service_manager import ServiceManager

import cherrypy
from rest.rest_serv import Server

logging.basicConfig(level=logging.INFO)
sm = ServiceManager()

# ROOM SPECIFIC "ventilation"


# THINGSPEAK_HOST = "THINGSPEAK_HOST"
# DEV_CONNECTOR_HOST = "DEVICE_CONNECTOR_HOST"
# TELEGRAM_HOST = "TELEGRAM_HOST"
# CATALOG_HOST = "CATALOG_HOST"


class SensorDataRetriever:
    def __init__(self):
        # for scope of this management we have three type of sensors values to consider
        # co2, temp and humidity
        # we have to consider all the plants in the room for this one
        self.sensors = ["co2", "temp", "humid"]
        self.data = dict()

        self.night_start = datetime.time(20, 0)  # 8:00 PM
        self.night_end = datetime.time(6, 0)     # 6:00 AM
        self.last = 2

    def is_night(self):
        now = datetime.datetime.now().time()
        return self.night_start <= now or now <= self.night_end

    def night_start(self):
        now = datetime.datetime.now()
        start_of_night = datetime.datetime(now.year, now.month, now.day, 20, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        return start_of_night

    def day_start(self):
        now = datetime.datetime.now()
        start_of_night = datetime.datetime(now.year, now.month, now.day, 6, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        return start_of_night

    def fetch_sensor_data(self, room, tower, shelf):

        tower = int(tower[-1])
        shelf = int(shelf[-1])

        for sensor in self.sensors:
            url_param = ""
            if sensor == "humid":
                if self.is_night():
                    start = self.night_start()
                else:
                    start = self.day_start()
                url_param = f"&start={start}"
            THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")
            url = f"{THINGSPEAK_HOST}/retrieve?room={room}&tower={tower}&shelf={shelf}&sensor={sensor}&last={self.last}{url_param}"
            response = requests.get(url)
            if response.status_code == 200:
                sensor_values = []
                for feed in response.json()["feeds"]:
                    sensor_values.append(float(feed["value"]))
                if len(sensor_values) != 0:
                    mean_values = sum(sensor_values)/len(sensor_values)
                    # mean_values = statistics.mean(sensor_values)
                    self.data[sensor] = mean_values
                else:
                    self.data[sensor] = 0.001

        return self.data



class CatalogIntegration:
    def fetch_plant_info(self):
        CATALOG_HOST = sm.service_base_url("catalog")
        url = f"{CATALOG_HOST}/all"
        response = requests.get(url)
        if response.status_code == 200:
            # pp(response.json())
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
    def __init__(self, low_CO2, high_CO2, low_temp, high_temp, humidity_day, humidity_night):
        self.low_CO2 = low_CO2
        self.high_CO2 = high_CO2
        self.low_temp = low_temp
        self.high_temp = high_temp
        self.humidity_day = humidity_day
        self.humidity_night = humidity_night



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
                    low_CO2=next(pn["low_CO2"] for pn in catalog_data["plant_nutrients"] if pn["type_id"]==type_id and pn["state"]==state),
                    high_CO2=next(pn["high_CO2"] for pn in catalog_data["plant_nutrients"] if pn["type_id"]==type_id and pn["state"]==state),
                    low_temp=next(pt["low_temp"] for pt in catalog_data["plant_types"] if pt["type_id"]==type_id),
                    high_temp=next(pt["high_temp"] for pt in catalog_data["plant_types"] if pt["type_id"]==type_id),
                    humidity_day=next(pt["humidity_day"] for pt in catalog_data["plant_types"] if pt["type_id"]==type_id),
                    humidity_night=next(pt["humidity_night"] for pt in catalog_data["plant_types"] if pt["type_id"]==type_id),
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

    def __init__(self):
        self.night_start = datetime.time(20, 0)  # 8:00 PM
        self.night_end = datetime.time(6, 0)     # 6:00 AM


    def is_night(self):
        now = datetime.datetime.now().time()
        return self.night_start <= now or now <= self.night_end


    def balanced_value(self, optimal_values, sensor_values):
        weighted_sum = 0
        total_weight = 0

        for opt_val, sensor_val in zip(optimal_values, sensor_values):
            weight = abs(opt_val - sensor_val)**2
            weighted_sum += opt_val * weight
            total_weight += weight
        
        balanced_value = weighted_sum/total_weight

        return balanced_value


    def accept_range(self, processed_data):
        room_processed_data = {}
        aggregated_data = defaultdict(list)

        for d in processed_data:
            temp_dict = {key: value for key, value in d.items() if key not in ['tower_id', 'shelf_id']}
            for key, value in temp_dict.items():
                aggregated_data[key].append(value)

        aggregated_data = dict(aggregated_data)

        for key in aggregated_data.keys():
            if key == "co2_sensor" or key == "temp_sensor":
                room_processed_data[key] = statistics.mean(aggregated_data[key])
            if key == "humid_sensor":
                room_processed_data[key] = aggregated_data[key]
            if key == "high_CO2":
                room_processed_data[key] = min(aggregated_data[key])
            if key == "low_CO2":
                room_processed_data[key] = max(aggregated_data[key])
            if key == "high_temp":
                room_processed_data[key] = min(aggregated_data[key])
            if key == "low_temp":
                room_processed_data[key] = max(aggregated_data[key])
            # for this one we minimize the sum of differences as the optimal value
            if key == "humidity_opt":
                optimal_values = aggregated_data["humidity_opt"]
                sensor_values = aggregated_data["humid_sensor"]
                room_processed_data[key] = self.balanced_value(optimal_values, sensor_values)

        return room_processed_data


    def process_sensor_data(self, farm, retriever, optimal_values_map):
        processed_data = []
        
        for shelf in farm.shelves:
            tower_id, shelf_id = shelf.shelf_id.split('-')
            sensor_data = retriever.fetch_sensor_data(room=1, tower=tower_id, shelf=shelf_id)
            logging.info(sensor_data)
            if sensor_data:
                optimal_values = optimal_values_map[shelf.shelf_id]
                d = {
                    "shelf_id": shelf_id,
                    "tower_id": tower_id,
                    "low_CO2": optimal_values.low_CO2,
                    "high_CO2": optimal_values.high_CO2,
                    "low_temp": optimal_values.low_temp,
                    "high_temp": optimal_values.high_temp,
                    "co2_sensor": float(sensor_data["co2"]),
                    "temp_sensor": float(sensor_data["temp"]),
                    "humid_sensor": float(sensor_data["humid"]),
                }
                if self.is_night():
                    d["humidity_opt"] = optimal_values.humidity_night
                else:
                    d["humidity_opt"] = optimal_values.humidity_day

                processed_data.append(d)

            else:
                logging.info(f"Failed to retrieve sensor data for Tower {tower_id}, Shelf {shelf_id}")
        
        # the data has to be processed for room in this scope of managmenet
        # the temp, co2 and humidity is shared in the room
        # also the ventilation is shared in the room
        # pick the max of low_x and min of high_x to have the safest band for all plants in this room
        room_processed_data = self.accept_range(processed_data)

        return processed_data, room_processed_data




class Notifier:

    def notify_user(self, room_id, payload):
        TELEGRAM_HOST = sm.service_base_url("telegram_interface")
        room_id = room_id[1:]
        url = f"{TELEGRAM_HOST}/notify_user?room={room_id}"
        resp = requests.post(url, json=payload)
        # logging.info(url)

    def set_catalog_ventilation(self, room_id, ventilation):
        CATALOG_HOST = sm.service_base_url("catalog")
        url_vent = f"{CATALOG_HOST}/rooms/{room_id}?ventilation={ventilation}"
        req_vent = requests.post(url_vent)
        logging.info(req_vent.json())
        if req_vent.status_code == 200:
            actuator = req_vent.json()["actuator_id"]
        return actuator, ventilation

    def set_device_status(self, actuator, command):
        payload = {}
        DEV_CONNECTOR_HOST = sm.service_base_url("device_connector_n", room_id="R1")
        # DEV_CONNECTOR_HOST = "http://10.241.43.254:8080"

        url_devices = f"{DEV_CONNECTOR_HOST}"
        payload["actuator"] = actuator        
        payload["command"] = command.lower()
        logging.info(payload)
        try:
            req = requests.post(url_devices, json=payload)
            req.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code.
            print(req.status_code)
            return req.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None


    def tasks(self, processed_data, room_processed_data):
        # pp(processed_data)
        # logging.info('\n')
        pp(room_processed_data)

        room_id = "R1" # or 1

        # # in case of implementation in Device Connector
        # topic = "pub/room1/tower1/shelf1"
        # mqt_pub.publish_to_topic(topic, processed_data)

        try:

            low_CO2 = room_processed_data["low_CO2"]
            high_CO2 = room_processed_data["high_CO2"]
            co2_sensor = round(room_processed_data["co2_sensor"], 2)

            low_temp = room_processed_data["low_temp"]
            high_temp = room_processed_data["high_temp"]
            temp_sensor = round(room_processed_data["temp_sensor"], 2)

            humid_sensor = round(max(room_processed_data["humid_sensor"]), 2)
            humidity_opt = room_processed_data["humidity_opt"]


            ventilations = 0
            ventilation = "OFF"
            if co2_sensor > high_CO2: 
                # the co2 in room is higher than it should be
                # ventilation = "ON"
                ventilations += 1

            if temp_sensor > high_temp:
                # the tempreture is higher than maximum accepted
                # ventilation = "ON"
                ventilations += 2

            # low humidity in the environment is generally more dangerous for plants
            if humid_sensor > humidity_opt:
                # ventilation = "ON"
                ventilations += 1

            if ventilations >= 2:
                # if two of the low priority conditions or/and a high priority condition triggered
                ventilation = "ON"

            # Craft informative message
            if ventilation == "ON":
                conditions_triggered = []
                if co2_sensor > high_CO2:
                    conditions_triggered.append(f"CO2 levels are too high (current: {co2_sensor}, threshold: {high_CO2})")
                if temp_sensor > high_temp:
                    conditions_triggered.append(f"Temperature is too high (current: {temp_sensor}°C, threshold: {high_temp}°C)")
                if humid_sensor > humidity_opt:
                    conditions_triggered.append(f"Humidity is above optimal levels (current: {humid_sensor}%, optimal: {humidity_opt}%)")
                
                conditions_str = "\n\n".join(conditions_triggered)
                message_to_user = f"Ventilation of room {room_id} is ON due to the following conditions:\n\n{conditions_str}."
            else:
                message_to_user = f"Ventilation of room {room_id} is OFF."


            # message_to_user = f"Ventilation of room {room_id} is {ventilation}"
            logging.info(message_to_user)
            self.notify_user(room_id, message_to_user)


            print("tyring to get the actuator")
            actuator, command = self.set_catalog_ventilation(room_id, ventilation)
            actuator = "ventilation_001"
            command = "OFF"
            self.set_device_status(actuator, command)


        except Exception as e:
            logging.info(e)




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