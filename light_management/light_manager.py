import time
from datetime import datetime
import requests
import random
import json
import logging
import threading

import cherrypy
from rest.rest_serv import Server

from pub import mqt_pub
from utils.service_manager import ServiceManager

logging.basicConfig(level=logging.INFO)
sm = ServiceManager()

# SHELF SPECIFIC "status_light" and "light"


# THINGSPEAK_HOST = "THINGSPEAK_HOST"
# DEV_CONNECTOR_HOST = "DEVICE_CONNECTOR_HOST"
# TELEGRAM_HOST = "TELEGRAM_HOST"
# CATALOG_HOST = "CATALOG_HOST"



class SensorDataRetriever:
    def __init__(self):
        # for scope of this management we have two type of sensors values to consider
        # light intensity for computing the total hours, height to compute the state of growth
        self.sensors = ["li", "height"]
        self.li_thresh = 50 # if the Light Intensity is below this value we consider the lights to be OFF (env light is still there)
        self.data = dict()


    def calculate_hours(self, feeds):
        # here would be the payload to be parsed for computing the total hours
        non_zero_duration = 0
        start_time = None
        light_on = False
        
        for feed in feeds:
            value = float(feed['value'])
            time = datetime.strptime(feed['time'], '%Y-%m-%dT%H:%M:%SZ')
            
            if value > self.li_thresh:
                if not light_on:
                    start_time = time
                    light_on = True
            else:
                if light_on:
                    non_zero_duration += (time - start_time).total_seconds() / 3600  # Convert to hours
                    light_on = False
        
        # If the last entry has a non-zero value and the light is on, add the duration up to now
        if light_on:
            non_zero_duration += (datetime.now() - start_time).total_seconds() / 3600  # Convert to hours
        
        return non_zero_duration


    def fetch_sensor_data(self, room, tower, shelf):
       
        tower = int(tower[-1])
        shelf = int(shelf[-1])
       
        for sensor in self.sensors:
            if sensor == "li":
                # in here I have to be able to retireve the data from the current day from start to finish of that day
                # first I have to know the day
                current_date = datetime.now().date()
                start_of_day = datetime.combine(current_date, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
                THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")
                url = f"{THINGSPEAK_HOST}/retrieve?room={room}&tower={tower}&shelf={shelf}&sensor={sensor}&start={start_of_day}"
                response = requests.get(url)
                if response.status_code == 200:
                    hours = self.calculate_hours(response.json()["feeds"])
                    self.data[sensor] = hours

            if sensor == "height":
                # based on the height I have to determine the state/stage of the growth
                # so for differet stages of growth we have different hours of light needed
                THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")
                url = f"{THINGSPEAK_HOST}/retrieve?room={room}&tower={tower}&shelf={shelf}&sensor={sensor}&last=10"
                response = requests.get(url)
                if response.status_code == 200:
                    heights = []
                    for feed in response.json()["feeds"]:
                        heights.append(float(feed["value"]))
                    if len(heights) != 0:
                        mean_height = sum(heights)/len(heights)
                        self.data[sensor] = mean_height
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
    def __init__(self, light_hours, vegetative_h, mature_h):
        self.light_hours = light_hours
        self.vegetative_h = vegetative_h
        self.mature_h = mature_h



class Farm:
    def __init__(self, shelves, optimal_values_map):
        self.shelves = shelves
        self.optimal_values_map = optimal_values_map

    @classmethod
    def initialize_from_catalog(cls, catalog_data):
        shelves = []
        optimal_values_map = {}
        
        for shelf_data in catalog_data["shelves"]:
            # print(shelf_data, "shelf datatatatatatatata")
            if shelf_data["room_id"] == "R1":
                shelf_id = f"{shelf_data['tower_id']}-{shelf_data['shelf_id']}"
                plant_id = shelf_data["plant_id"]
                state = shelf_data.get("status", "Unknown")
                type_id = next(plant["type_id"] for plant in catalog_data["plants"] if plant["plant_id"]==plant_id)
                optimal_values_map[shelf_id] = OptimalValues(
                    light_hours=next(pn["light"] for pn in catalog_data["plant_nutrients"] if pn["type_id"]==type_id and pn["state"]==state),
                    vegetative_h=next(pt["vegetative_h"] for pt in catalog_data["plant_types"] if pt["type_id"]==type_id),
                    mature_h=next(pt["mature_h"] for pt in catalog_data["plant_types"] if pt["type_id"]==type_id),
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
                    "light_hours_catalog": optimal_values.light_hours,
                    "light_hours_sensor": float(sensor_data["li"]),
                    "shelf_height": float(sensor_data["height"]),
                    "vegetative_h": optimal_values.vegetative_h,
                    "mature_h": optimal_values.mature_h
                })
            else:
                logging.info(f"Failed to retrieve sensor data for Tower {tower_id}, Shelf {shelf_id}")
        return processed_data



class Notifier:

    def set_catalog_status(self, room_id, tower_id, shelf_id, status, status_light):
        CATALOG_HOST = sm.service_base_url("catalog")
        url_status = f"{CATALOG_HOST}/shelves/{room_id}/{tower_id}/{shelf_id}?status={status}"
        url_status_light = f"{CATALOG_HOST}/shelves/{room_id}/{tower_id}/{shelf_id}?status_light={status_light}"
        # print(url_status)
        # print(url_status_light)

        # this part only sets the catalog status
        req_status = requests.post(url_status)
        time.sleep(1)
        # this part sets the catalog light_status, in response it takes the "actuator_id" to actually deactivate/activate actuators/devices
        req_status_light = requests.post(url_status_light)
        if req_status_light.status_code == 200:
            actuator = req_status_light.json()["status_light_id"]

        # logging.info(url_status, url_status_light)
        return actuator, status_light


    def set_catalog_light(self, room_id, tower_id, shelf_id, light):
        CATALOG_HOST = sm.service_base_url("catalog")
        url_light = f"{CATALOG_HOST}/shelves/{room_id}/{tower_id}/{shelf_id}?light={light}"

        # this part sets the catalog light_status, in response it takes the "actuator_id" to actually deactivate/activate actuators/devices
        req_light = requests.post(url_light)
        if req_light.status_code == 200:
            actuator = req_light.json()["light_id"]

        return actuator, light


    def set_device_status(self, actuator, command):
        payload = {}
        DEVICE_CONNECTOR_HOST = sm.service_base_url("device_connector_n")
        url_devices = f"{DEV_CONNECTOR_HOST}"
        payload["actuator"] = actuator
        payload["command"] = command.lower()
        logging.info(payload)
        req = requests.post(url_devices, json=self.device_payload)


    def notify_user(self, room_id, payload):
        TELEGRAM_HOST = sm.service_base_url("telegram_interface")
        room_id = room_id[1:]
        url = f"{TELEGRAM_HOST}/notify_user?room={room_id}"
        resp = requests.post(url, json=payload)
        logging.info(url)

    def tasks(self, processed_data):

        # pp(processed_data)
        # topic = "pub/room1/tower1/shelf1"
        # mqt_pub.publish_to_topic(topic, processed_data)

        room_id = "R1"
        # self.notify_user(room_id, "message to user to show lm working")

        for data in processed_data:
            shelf_id = data["shelf_id"]
            tower_id = data["tower_id"]
            light_hours_catalog = data["light_hours_catalog"]
            light_hours_sensor = data["light_hours_sensor"]
            shelf_height = data["shelf_height"]
            vegetative_h = data["vegetative_h"]
            mature_h = data["mature_h"]

            # Notify user through User Awareness endpoints here...
            # Notifying user could be a simple report what has been done (e.g. tX/sX is vegetative, light is ON for tX/sX etc.)
            # Light Manager should set status light based on heights
            # (Seeding:GREEN, Vegetative:YELLOW, Mature:RED) (Did not the endpoint and correct format to set the light)
            # Light Manager also sets the status in Catalog (Did not find the endpoint to update the status)
            # Light Manager should set the lights to ON or OFF based on the optimal hours and sensor hours (Did not find the endpoint and correct format)


            logging.info(f"Tower {tower_id}, Shelf {shelf_id}:")


            logging.info(f"Current Height: {shelf_height}, Also the Vegetative height: {vegetative_h} and Mature Height: {mature_h}")
            # to set the status (in CATALOG) and status_light (DEVICE_CONNECTOR)
            if shelf_height < vegetative_h:
                # then plant is seeding
                status = "Seeding"
                status_light = "GREEN"
            if (shelf_height > vegetative_h) and (shelf_height < mature_h):
                # then plant is vegetative
                status = "Vegetative"
                status_light = "YELLOW"

            if shelf_height > mature_h:
                # then plant is mature, have to notify user as well
                status = "Mature"
                status_light = "RED"
                message_to_user = f"Plant in tower {tower_id} and shelf {shelf_id} is fully grown."
                self.notify_user(room_id, message_to_user)
                logging.info(message_to_user)

            # this part sets the catalog status and set the devices LEDs for status based on the their growing stage (based on the height)
            try:
                actuator, command = self.set_catalog_status(room_id, tower_id, shelf_id, status, status_light)
                self.set_device_status(actuator, command)
            except Exception as e:
                print(str(e))
            # logging.info('\n')



            logging.info(f"Optimal Light Hours: {light_hours_catalog}, Sensor Light Hours: {light_hours_sensor}")
            # to set the main light in shelves
            if light_hours_sensor < light_hours_catalog:
                # then the shelf light should be ON, the plants didn't get enough daily light hours
                light = "ON"
            else:
                # then the shelf light should be OFF, the plants got enough daily light hours
                light = "OFF"

            # this part sets the catalog light and set the devices LEDs for main light (based on daily hours of needed light)
            try:
                actuator, command = self.set_catalog_light(room_id, tower_id, shelf_id, light)
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