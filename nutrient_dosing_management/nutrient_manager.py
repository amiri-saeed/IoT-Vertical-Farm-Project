import time
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


# JUST INFORMING USER THROUGH TELEGRAM


# THINGSPEAK_HOST = "THINGSPEAK_HOST"
# DEV_CONNECTOR_HOST = "DEVICE_CONNECTOR_HOST"
# TELEGRAM_HOST = "TELEGRAM_HOST"



class SensorDataRetriever:
    def __init__(self):
        self.sensors = ["n", "p", "k", "ph"]
        self.data = dict()

    def fetch_sensor_data(self, room, tower, shelf, last):
        
        tower = int(tower[-1])
        shelf = int(shelf[-1])

        for sensor in self.sensors:
            # logging.info(sensor, tower, shelf)
            logging.info("Sensor: %s, Tower: %d, Shelf: %d", sensor, tower, shelf)
            THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")
            url = f"{THINGSPEAK_HOST}/retrieve?room={room}&tower={tower}&shelf={shelf}&sensor={sensor}&last={last}"
            response = requests.get(url)
            if response.status_code == 200:
                print(response.json())
                vals = []
                for feed in response.json()["feeds"]:
                    vals.append(float(feed["value"]))
                if len(vals) != 0:
                    mean_value = float(sum(vals))/len(vals)
                    self.data[sensor] = mean_value
                else:
                    self.data[sensor] = 0.001
        else:
            print("something went wrong....")
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


class OptimalValues:
    def __init__(self, ph_low, ph_high, n, p, k):
        self.ph_low = ph_low
        self.ph_high = ph_high
        self.n = n
        self.p = p
        self.k = k


class Shelf:
    def __init__(self, shelf_id, plant_id, status, light, status_light, water_pump):
        self.shelf_id = shelf_id
        self.plant_id = plant_id
        self.status = status
        self.light = light
        self.status_light = status_light
        self.water_pump = water_pump


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
                type_id = next(plant["type_id"] for plant in catalog_data["plants"] if plant["plant_id"] == plant_id)
                optimal_values_map[shelf_id] = OptimalValues(
                    ph_low=next(pt["low_ph"] for pt in catalog_data["plant_types"] if pt["type_id"] == type_id),
                    ph_high=next(pt["high_ph"] for pt in catalog_data["plant_types"] if pt["type_id"] == type_id),
                    n=next(pn["N"] for pn in catalog_data["plant_nutrients"] if pn["type_id"] == type_id and pn["state"]==state),
                    p=next(pn["P"] for pn in catalog_data["plant_nutrients"] if pn["type_id"] == type_id and pn["state"]==state),
                    k=next(pn["K"] for pn in catalog_data["plant_nutrients"] if pn["type_id"] == type_id and pn["state"]==state)
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
            sensor_data = retriever.fetch_sensor_data(room=1, tower=tower_id, shelf=shelf_id, last=1)
            if sensor_data:
                optimal_values = optimal_values_map[shelf.shelf_id]
                processed_data.append({
                    "shelf_id": shelf_id,
                    "tower_id": tower_id,
                    "ph_high_catalog": optimal_values.ph_high,
                    "ph_low_catalog": optimal_values.ph_low,
                    "ph_sensor": float(sensor_data["ph"]),
                    "n_catalog": optimal_values.n,
                    "n_sensor": float(sensor_data["n"]),
                    "p_catalog": optimal_values.p,
                    "p_sensor": float(sensor_data["p"]),
                    "k_catalog": optimal_values.k,
                    "k_sensor": float(sensor_data["k"]),
                })
            else:
                logging.info(f"Failed to retrieve sensor data for Tower {tower_id}, Shelf {shelf_id}")
        return processed_data


class UserNotifier:
    def __init__(self):
        messages_path = "msg_to_user.json"
        self.messages = self._read_messages(messages_path)

    def _read_messages(self, path):
        with open(path, "r") as json_data:
            return json.load(json_data)["messages"]

    def notify_users(self, processed_data):

        # topic = "pub/room1/tower1/shelf1"
        # mqt_pub.publish_to_topic(topic, processed_data)

        room_id = 1


        for data in processed_data:
            # print(data, "nutrient manager, room proccesed data")
            shelf_id = data["shelf_id"]
            tower_id = data["tower_id"]
            ph_low_catalog = data["ph_low_catalog"]
            ph_high_catalog = data["ph_high_catalog"]
            ph_sensor = round(data["ph_sensor"], 2)
            n_catalog = data["n_catalog"]
            n_sensor = round(data["n_sensor"], 2)
            p_catalog = data["p_catalog"]
            p_sensor = round(data["p_sensor"], 2)
            k_catalog = data["k_catalog"]
            k_sensor = round(data["k_sensor"], 2)

            message_events = []
            
            if ph_sensor > ph_high_catalog * 1.1:
                for event in self.messages:
                    if event["event"] == "ph_higher":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, ph_low_catalog=ph_low_catalog, ph_high_catalog=ph_high_catalog, ph_sensor=ph_sensor)
                        message_events.append(msg)
            if ph_sensor < ph_low_catalog * 0.9:
                for event in self.messages:
                    if event["event"] == "ph_lower":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, ph_low_catalog=ph_low_catalog, ph_high_catalog=ph_high_catalog, ph_sensor=ph_sensor)
                        message_events.append(msg)

            # check the 10 percents higher/lower than optimal values
            if n_sensor > n_catalog * 1.1:
                for event in self.messages:
                    if event["event"] == "n_higher":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, n_catalog=n_catalog, n_sensor=n_sensor)
                        message_events.append(msg)
            if n_sensor < n_catalog * 0.9:
                for event in self.messages:
                    if event["event"] == "n_lower":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, n_catalog=n_catalog, n_sensor=n_sensor)
                        message_events.append(msg)

            # check the 10 percents higher/lower than optimal values
            if p_sensor > p_catalog * 1.1:
                for event in self.messages:
                    if event["event"] == "p_higher":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, p_catalog=p_catalog, p_sensor=p_sensor)
                        message_events.append(msg)
            elif p_sensor < p_catalog * 0.9:
                for event in self.messages:
                    if event["event"] == "p_lower":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, p_catalog=p_catalog, p_sensor=p_sensor)
                        message_events.append(msg)

            # check the 10 percents higher/lower than optimal values
            if k_sensor > k_catalog * 1.1:
                for event in self.messages:
                    if event["event"] == "k_higher":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, k_catalog=k_catalog, k_sensor=k_sensor)
                        message_events.append(msg)
            elif k_sensor < k_catalog * 0.9:
                for event in self.messages:
                    if event["event"] == "k_lower":
                        msg = event["msg"].format(tower_id=tower_id, shelf_id=shelf_id, k_catalog=k_catalog, k_sensor=k_sensor)
                        message_events.append(msg)

            logging.info(f"Tower {tower_id}, Shelf {shelf_id}:")
            logging.info(f"Optimal pH band: {ph_low_catalog}-{ph_high_catalog}, Sensor pH: {ph_sensor}")
            logging.info(f"Optimal N: {n_catalog}, Sensor N: {n_sensor}")
            logging.info(f"Optimal P: {p_catalog}, Sensor P: {p_sensor}")
            logging.info(f"Optimal K: {k_catalog}, Sensor K: {k_sensor}")

            message_to_send = '\n\n'.join(message_events)
            logging.info(message_to_send)

            TELEGRAM_HOST = sm.service_base_url("telegram_interface")
            url = f"{TELEGRAM_HOST}/notify_user?room={room_id}"
            resp = requests.post(url, json=message_to_send)
            if resp.status_code == 200:
                logging.info("notification was sent to user.")




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