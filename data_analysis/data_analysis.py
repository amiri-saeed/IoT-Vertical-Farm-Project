import json
import threading
import datetime
import statistics
import random
import io
import base64 as bs4
import logging

import cherrypy
import requests

import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from matplotlib import style 

from rest.rest_serv import AnalysisServ
from utils.service_manager import ServiceManager

logging.basicConfig(level=logging.INFO)
sm = ServiceManager()


# THINGSPEAK_HOST = "THINGSPEAK_HOST"


class DataAnalysis:

    def __init__(self):
        self._read_sensors()
        # self.sm = service_manager
        self.required_params_shelf = ["room", "tower", "shelf", "sensor"]
        self.required_params_room = ["room", "sensor"]
        self.num_towers = 2
        self.num_shelves = 2
        
        self.fig_x = 12
        self.fig_y = 7
        

    def _read_sensors(self):
        with open("sensors.json", "r") as file:
            self.sensors = json.load(file)

    def _check_datetime_format(self, datetime_str):
        format_str = "%Y-%m-%d %H:%M:%S"
        try:
            datetime.datetime.strptime(datetime_str, format_str)
            return True
        except ValueError:
            return False
            

    # def _params_to_url(self, params):
    #     keys = params.keys()

    #     # to check for the required params
    #     list_of_sensors = False
    #     if "sensor" in keys:
    #         sensor = params["sensor"]
    #         if "," in sensor:
    #             list_of_sensors = True
    #             sensors = sensor.split(",")
    #             for sensor in sensors:
    #                 if sensor in self.sensors["fixed"]:
    #                     # check for required params of a shelf specific sensor
    #                     if not all(key in keys for key in self.required_params_shelf):
    #                         return "Wrong keys."
    #                     else:
    #                         room_id = params["room"]
    #                         tower_id = params.get("tower", 0)
    #                         shelf_id = params.get("shelf", 0)
    #                 elif sensor in self.sensors["unfixed"]:
    #                     # check for required params of a room specific sensor
    #                     if not all(key in keys for key in self.required_params_room):
    #                         return "Wrong keys."
    #                     else:
    #                         room_id = params["room"]
    #                         # since the value does not matter in this case
    #                         # thingspeak adaptor would not parse this part
    #                         tower_id = 0
    #                         shelf_id = 0
    #                 else:
    #                     return "Wrong sensor. Not all from list of shelf specific."
            
    #         # single sensor
    #         else:
    #             if sensor in self.sensors["fixed"]:
    #                 # check for required params of a shelf specific sensor
    #                 if all(key in keys for key in self.required_params_room):
    #                     room_id = params["room"]
    #                     # since the value does not matter in this case
    #                     # thingspeak adaptor would not parse this part
    #                     tower_id = 0
    #                     shelf_id = 0

    #                 else:
    #                     room_id = params["room"]
    #                     tower_id = params.get("tower", 0)
    #                     shelf_id = params.get("shelf", 0)
    #             elif sensor in self.sensors["unfixed"]:
    #                 # check for required params of a room specific sensor
    #                 if not all(key in keys for key in self.required_params_room):
    #                     return "Wrong keys."
    #                 else:
    #                     room_id = params["room"]
    #                     # since the value does not matter in this case
    #                     # thingspeak adaptor would not parse this part
    #                     tower_id = 0
    #                     shelf_id = 0
    #             else:
    #                 return "Wrong sensor."

    #     # check for the optional params
    #     if "start" in keys:
    #         if self._check_datetime_format(params["start"]):
    #             start = params["start"]
    #         else:
    #             return "Wrong time format. Maybe use '-' instead of '/'?"
    #     else:
    #         # if start not included, the least recent time is considered with some old time
    #         start = datetime.datetime(1970, 1, 1, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")

    #     if "end" in keys:
    #         if self.check_datetime_format(params["end"]):
    #             end = params["end"]
    #         else:
    #             return "Wrong time format. Maybe use '-' instead of '/'?"
    #     else:
    #         # if end not included, the most recent time is considered
    #         end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    #     THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")
    #     if list_of_sensors:
    #         # the case of comparing multiple sensors in one tower/shelf
    #         urls = []
    #         for sensor in sensors:
    #             url = f"{THINGSPEAK_HOST}/retrieve?room={room_id}&tower={tower_id}&shelf={shelf_id}&sensor={sensor}&start={start}&end={end}"
    #             urls.append(url)
    #         url = urls
    #     elif room_id and not tower_id and not shelf_id:
    #         # Generate a list of URLs for all shelves and towers in the room with one sensor
    #         urls = []
    #         for tower_id in range(1, self.num_towers + 1):
    #             for shelf_id in range(1, self.num_shelves + 1):
    #                 url = f"{THINGSPEAK_HOST}/retrieve?room={room_id}&tower={tower_id}&shelf={shelf_id}&sensor={sensor}&start={start}&end={end}"
    #                 urls.append(url)
    #         url = urls
    #     else:
    #         url = f"{THINGSPEAK_HOST}/retrieve?room={room_id}&tower={tower_id}&shelf={shelf_id}&sensor={sensor}&start={start}&end={end}"
        
    #     print(url, "UUUUUUUUUUUUUUUUUUUURRRRRRRRRRRRRRRRRRRRRRRRRRRRLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
    #     return url

    def _params_to_url(self, params):
        keys = params.keys()

        if "start" in keys:
            if self._check_datetime_format(params["start"]):
                start = params["start"]
            else:
                return "Wrong time format. Maybe use '-' instead of '/'?"
        else:
            # if start not included, the least recent time is considered with some old time
            start = datetime.datetime(1970, 1, 1, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")

        if "end" in keys:
            if self.check_datetime_format(params["end"]):
                end = params["end"]
            else:
                return "Wrong time format. Maybe use '-' instead of '/'?"
        else:
            # if end not included, the most recent time is considered
            end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")

        room_id = params["room"][-1]
        if "tower" in keys:
            tower_id = params["tower"][-1]
        else:
            tower_id = 0

        if "shelf" in keys:
            shelf_id = params["shelf"][-1]
        else:
            shelf_id = 0

        sensor = params["sensor"]

        # if tower_id != 0 and shelf_id != 0:
        url = f"{THINGSPEAK_HOST}/retrieve?room={room_id}&tower={tower_id}&shelf={shelf_id}&sensor={sensor}&start={start}&end={end}"
        # else:
        #     url = f"{THINGSPEAK_HOST}/retrieve?room={room_id}&sensor={sensor}&start={start}&end={end}"

        return url


    # def _params_to_url_shlv(self, params):
    #     print(params, "paramaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaassssssssssssssaaaaaaaaaaaaaaaaaaaaaaassssssssssssss")
    #     keys = params.keys()

    #     if "start" in keys:
    #         if self._check_datetime_format(params["start"]):
    #             start = params["start"]
    #         else:
    #             return "Wrong time format. Maybe use '-' instead of '/'?"
    #     else:
    #         # if start not included, the least recent time is considered with some old time
    #         start = datetime.datetime(1970, 1, 1, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")

    #     if "end" in keys:
    #         if self.check_datetime_format(params["end"]):
    #             end = params["end"]
    #         else:
    #             return "Wrong time format. Maybe use '-' instead of '/'?"
    #     else:
    #         # if end not included, the most recent time is considered
    #         end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #     THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")

    #     room_id = params["room"]
    #     if "tower" in keys:
    #         tower_id = params["tower"]
    #     else:
    #         tower_id = 0

    #     if "shelf" in keys:
    #         shelf_id = params["shelf"]
    #     else:
    #         shelf_id = 0

    #     sensor = params["sensor"]

    #     url = f"{THINGSPEAK_HOST}/retrieve?room={room_id}&tower={tower_id}&shelf={shelf_id}&sensor={sensor}&start={start}&end={end}"

        return url

    def _params_to_url_shlvs(self, params):
        keys = params.keys()

        if "start" in keys:
            if self._check_datetime_format(params["start"]):
                start = params["start"]
            else:
                return "Wrong time format. Maybe use '-' instead of '/'?"
        else:
            # if start not included, the least recent time is considered with some old time
            start = datetime.datetime(1970, 1, 1, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")

        if "end" in keys:
            if self.check_datetime_format(params["end"]):
                end = params["end"]
            else:
                return "Wrong time format. Maybe use '-' instead of '/'?"
        else:
            # if end not included, the most recent time is considered
            end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        THINGSPEAK_HOST = sm.service_base_url("thingspeak_adaptor")

        room_id = params["room"][-1]
        if "tower" in keys:
            tower_id = params["tower"][-1]
        else:
            tower_id = 0

        if "shelf" in keys:
            shelf_id = params["shelf"][-1]
        else:
            shelf_id = 0

        sensor = params["sensor"]

        urls = []
        for tower_id in range(1, self.num_towers + 1):
            for shelf_id in range(1, self.num_shelves + 1):
                url = f"{THINGSPEAK_HOST}/retrieve?room={room_id}&tower={tower_id}&shelf={shelf_id}&sensor={sensor}&start={start}&end={end}"
                urls.append(url)

        return urls


    def json_to_xy(self, json_resp):
        print(json_resp)
        feeds = json_resp["feeds"]
        print(feeds)
        x = [float(x["value"]) for x in feeds]
        y = [datetime.datetime.strptime(y["time"], '%Y-%m-%dT%H:%M:%SZ') for y in feeds]
        return x, y


    def plot_xy(self, x, y, sensor_name, base64=True):

        plt.style.use("fivethirtyeight")
        plt.figure(figsize=(self.fig_x, self.fig_y))
        plt.plot(y, x)
        plt.xticks(rotation=60)
        plt.xlabel("Time")
        plt.ylabel(sensor_name.capitalize())
        plt.legend()
        plt.tight_layout()
        plt.grid()

        if base64:
            my_stringIObytes = io.BytesIO()
            plt.savefig(my_stringIObytes, format='jpg')
            my_stringIObytes.seek(0)
            my_base64_jpgData = bs4.b64encode(my_stringIObytes.read()).decode()
            return my_base64_jpgData
        else:
            return plt



    def plot_multiple_xy(self, xs, ys, sensor_names, base64_encode=True, title=''):
        plt.style.use("fivethirtyeight")
        plt.figure(figsize=(self.fig_x, self.fig_y))

        for i, (x, y) in enumerate(zip(xs, ys)):
            plt.plot(y, x, label=sensor_names[i])

        plt.xticks(rotation=60)
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.title(title)
        plt.legend()
        plt.tight_layout()
        plt.grid()

        if base64_encode:
            my_stringIObytes = io.BytesIO()
            plt.savefig(my_stringIObytes, format='jpg')
            my_stringIObytes.seek(0)
            my_base64_jpgData = bs4.b64encode(my_stringIObytes.read()).decode()
            plt.close()
            return my_base64_jpgData
        else:
            return plt



    def serve_avg(self, params):
        response = {}
        url = self._params_to_url(params)
        req = requests.get(url).json()
        # req = RESP
        x, y = self.json_to_xy(req)
        if len(x) != 0:
            average = sum(x)/len(x)
            response["avg"] = average
        else:
            response["avg"] = "non existant"
        return response


    def serve_max(self, params):
        response = {}
        url = self._params_to_url(params)
        req = requests.get(url).json()
        # req = RESP
        x, y = self.json_to_xy(req)
        if len(x) != 0:
            maximum = max(x)
            response["max"] = maximum
        else:
            response["max"] = "non existant"
        return response


    def serve_min(self, params):
        response = {}
        url = self._params_to_url(params)
        req = requests.get(url).json()
        # req = RESP
        x, y = self.json_to_xy(req)
        if len(x) != 0:
            minimum = min(x)
            response["min"] = minimum
        else:
            response["min"] = "non existant"
        return response


    def serve_plt(self, params):
        url = self._params_to_url(params)
        sensor = params["sensor"]
        req = requests.get(url).json()
        x, y = self.json_to_xy(req)
        base64_rep = self.plot_xy(x, y, sensor, base64=True)
        response = {"bs4_img": base64_rep}
        return response


    # def serve_comp_plt_shlv(self, params):
    #     xys = []
    #     url = self._params_to_url_shlv(params)

    #     if isinstance(url, list):
    #         sensors = params["sensor"].split(",")
    #         # for sensor in sensors:
    #         for i, u in enumerate(url):
    #             req = requests.get(u).json()
    #             # req = resps[i]
    #             x, y = self.json_to_xy(req)
    #             xys.append((x, y))

    #     xs = [xy[0] for xy in xys]  # Extract x values from x, y pairs
    #     y = xys[0][1]  # Extract y values from the first x, y pair (assuming y values are the same for all x arrays)
    #     print(y, "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
    #     sensor_names = [sensor for sensor in sensors]  # Replace `sensor_names` with your list of sensor names

    #     base64_rep = self.plot_multiple_xy(xs, y, sensor_names, base64_encode=True)
    #     response = {"bs4_img": base64_rep}
       
    #     return response


    def serve_comp_plt_shlvs(self, params):
        xys = []
        urls = self._params_to_url_shlvs(params)
        print(urls)
        sensor = params["sensor"]
        for url in urls:
            req = requests.get(url).json()
            x, y = self.json_to_xy(req)
            xys.append((x, y))

        xs, ys = zip(*xys)  # Separate the x and y values from the input data
        shelf_tower_combinations = [f"shelf: {shelf_id}, tower: {tower_id}" for shelf_id in range(1, self.num_shelves + 1) for tower_id in range(1, self.num_towers + 1)]
        title = f"{sensor}'s data"
        base64_rep = self.plot_multiple_xy(xs, ys, shelf_tower_combinations, base64_encode=True, title=title)
        response = {"bs4_img": base64_rep}
        return response


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
        cherrypy.tree.mount(AnalysisServ(self), '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()


    def start_rest(self, SERVICE_RNET, SERVICE_PORT):
        threading.Thread(target=self.rest_serv, kwargs={'SERVICE_RNET': SERVICE_RNET, 'SERVICE_PORT': SERVICE_PORT}).start()
