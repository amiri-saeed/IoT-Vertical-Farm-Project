import requests
import json
import logging
import io
import base64
from PIL import Image

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent

import cherrypy
from rest.rest_serv import NotificationServ
from utils.service_manager import ServiceManager

logging.basicConfig(level=logging.INFO)
sm = ServiceManager()

# DATA_ANALYSIS_HOST = sm.service_base_url("data_analysis")


class SmartGardenBot:
    def __init__(self, token):
        self.bot = telepot.Bot(token)
        self.user_data = {}  # Dictionary to store user choices

        # Define room-specific and shelf-specific sensors
        self.room_specific = ['temp', 'humid', 'co2', 'water']
        self.shelf_specific = ['ph', 'moisture', 'n', 'p', 'k', 'height', 'li']
        self.sensors_dict = {
            "temp": "Temperature",
            "humid": "Humidity",
            "co2": "CO2",
            "water": "Water Tank",
            "ph": "pH",
            "moisture": "Moisture",
            "n": "Nitrogen (N)",
            "p": "Phosphorus (P)",
            "k": "Potassium (K)",
            "height": "Height",
            "li": "Light Intensity"
        }

        MessageLoop(self.bot, {
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query
        }).run_as_thread()

        logging.info('Listening for commands...')

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type == 'text':
            command = msg['text'].split()[0]

            if command.startswith('/start'):
                self.save_chat_id(chat_id)  # Save the chat ID in a JSON file
                self.bot.sendMessage(chat_id, "Welcome!")
            elif command.startswith('/help'):
                self.bot.sendMessage(chat_id, "Available commands:\n"
                                              "/plot to generate plot of a given sensor in the room/tower/shelf\n"
                                              "/compare_shelves to generate plot of a given sensor in different shelves of a room\n"
                                              "/avg to reply with the avg value of a given sensor in a room/tower/shelf\n"
                                              "/min to reply with the minimum value of a given sensor in a room/tower/shelf\n"
                                              "/max to reply with the maximum value of a given sensor in a room/tower/shelf")
            elif command.startswith('/plot'):
                self.user_data[chat_id] = {'command': 'plot'}
                self.show_rooms(chat_id)
            elif command.startswith('/compare_shelves'):
                self.user_data[chat_id] = {'command': 'compare_shelves'}
                self.show_rooms(chat_id)
            elif command.startswith('/avg'):
                self.user_data[chat_id] = {'command': 'avg'}
                self.show_rooms(chat_id)
            elif command.startswith('/min'):
                self.user_data[chat_id] = {'command': 'min'}
                self.show_rooms(chat_id)
            elif command.startswith('/max'):
                self.user_data[chat_id] = {'command': 'max'}
                self.show_rooms(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Invalid command. Use /help for available commands.")

    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        command, choice = data.split('_')

        if command == 'room':
            self.user_data[from_id]['room'] = choice
            self.show_sensors(from_id)
        elif command == 'sensor':
            if self.user_data[from_id].get('selecting_sensors'):
                if choice == 'done':
                    self.user_data[from_id]['selecting_sensors'] = False
                    self.show_towers(from_id)
                else:
                    self.user_data[from_id]['sensors'].append(choice)
                    self.show_sensors(from_id, partial_selection=True)
            else:
                self.user_data[from_id]['sensor'] = choice
                if choice in self.room_specific:
                    self.process_command(from_id)
                else:
                    if self.user_data[from_id]['command'] in ['plot', 'avg', 'min', 'max']:
                        self.show_towers(from_id)
                    elif self.user_data[from_id]['command'] == 'compare_shelves':
                        self.process_command(from_id)
        elif command == 'tower':
            self.user_data[from_id]['tower'] = choice
            self.show_shelves(from_id)
        elif command == 'shelf':
            self.user_data[from_id]['shelf'] = choice
            self.process_command(from_id)

    def show_rooms(self, chat_id):
        rooms = ['Room1']
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=room, callback_data=f'room_{room}') for room in rooms]
        ])
        self.bot.sendMessage(chat_id, 'Choose a room:', reply_markup=keyboard)

    def show_towers(self, chat_id):
        towers = ['Tower1', 'Tower2']
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=tower, callback_data=f'tower_{tower}') for tower in towers]
        ])
        self.bot.sendMessage(chat_id, 'Choose a tower:', reply_markup=keyboard)

    def show_shelves(self, chat_id):
        shelves = ['Shelf1', 'Shelf2']
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=shelf, callback_data=f'shelf_{shelf}') for shelf in shelves]
        ])
        self.bot.sendMessage(chat_id, 'Choose a shelf:', reply_markup=keyboard)

    def show_sensors(self, chat_id, partial_selection=False):
        

        if self.user_data[chat_id].get('command') in ['compare_sensors', 'compare_shelves']:
            sensors = self.shelf_specific
        else:
            sensors = self.room_specific + self.shelf_specific

        keyboard_buttons = [
            [InlineKeyboardButton(text=self.sensors_dict[sensor], callback_data=f'sensor_{sensor}') for sensor in sensors[:3]],
            [InlineKeyboardButton(text=self.sensors_dict[sensor], callback_data=f'sensor_{sensor}') for sensor in sensors[3:6]],
            [InlineKeyboardButton(text=self.sensors_dict[sensor], callback_data=f'sensor_{sensor}') for sensor in sensors[6:9]],
            [InlineKeyboardButton(text=self.sensors_dict[sensor], callback_data=f'sensor_{sensor}') for sensor in sensors[9:]]
        ]
        
        if partial_selection:
            keyboard_buttons.append([InlineKeyboardButton(text="Done", callback_data='sensor_done')])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        self.bot.sendMessage(chat_id, 'Choose a sensor:' if not partial_selection else 'Choose more sensors or press Done:', reply_markup=keyboard)

    def process_command(self, chat_id):
        choices = self.user_data[chat_id]
        # self.bot.sendMessage(chat_id, choices)
        command = choices['command']
        room = int(choices.get('room', '').replace("Room", ""))
        sensors = choices.get('sensors', [])
        sensor = choices.get('sensor', '')
        tower = choices.get("tower", "")
        shelf = choices.get("shelf", "")

        if tower != "":
            tower = int(choices.get('tower', '').replace("Tower", ""))
        if shelf != "":
            shelf = int(choices.get('shelf', '').replace("Shelf", ""))

        if command == 'plot':
            img = self.generate_plot(room, sensor, tower, shelf)
            if img:
                self.bot.sendPhoto(chat_id, img)
            else:
                self.bot.sendMessage(chat_id, "Failed to generate plot.")
        elif command == 'compare_shelves':
            img = self.compare_shelves(room, sensor)
            if img:
                self.bot.sendPhoto(chat_id, img)
            else:
                self.bot.sendMessage(chat_id, "Failed to generate comparison plot.")
        elif command == 'compare_sensors':
            img = self.compare_sensors(room, sensors)
            if img:
                self.bot.sendPhoto(chat_id, img)
            else:
                self.bot.sendMessage(chat_id, "Failed to generate comparison plot.")
        elif command in ['avg', 'min', 'max']:
            response = self.get_stat(room, sensor, tower, shelf, command)
            self.bot.sendMessage(chat_id, response)

    def generate_plot(self, room, sensor, tower='', shelf=''):
        DATA_ANALYSIS_HOST = sm.service_base_url("data_analysis")
        url = f"{DATA_ANALYSIS_HOST}/plot"
        params = {"room": room, "sensor": sensor}
        if sensor in self.shelf_specific:
            params.update({"tower": tower, "shelf": shelf})
        response = requests.get(url, params=params)
        if response.status_code == 200:
            plot_data = response.json()
            plot_image = plot_data["bs4_img"]
            img = self.decode_base64_img(plot_image)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            image_file = io.BytesIO(img_byte_arr)
            return image_file
        else:
            return None

    def compare_shelves(self, room, sensor):
        DATA_ANALYSIS_HOST = sm.service_base_url("data_analysis")
        url = f"{DATA_ANALYSIS_HOST}/plot_compare_shelves"
        params = {"room": room, "sensor": sensor}
        response = requests.get(url, params=params)
        print(response.json(), "resposnesejnaeipsfhaeipsfhpsoieeeeeeeee")
        if response.status_code == 200:
            plot_data = response.json()
            plot_image = plot_data["bs4_img"]
            img = self.decode_base64_img(plot_image)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            image_file = io.BytesIO(img_byte_arr)
            return image_file
        else:
            return None

        ## for testing purposes
        # with open("plot_base64.json", "r", encoding='utf-8') as file:
        #     # Load the JSON data
        #     content = file.read()
        #     plot_data = json.loads(content)

        # plot_image = plot_data["bs4_img"]
        # img = self.decode_base64_img(plot_image)
        # img_byte_arr = io.BytesIO()
        # img.save(img_byte_arr, format='JPEG')
        # img_byte_arr = img_byte_arr.getvalue()
        # image_file = io.BytesIO(img_byte_arr)
        # return image_file


    def compare_sensors(self, room, sensors):
        DATA_ANALYSIS_HOST = sm.service_base_url("data_analysis")
        url = f"{DATA_ANALYSIS_HOST}/plot_compare_shelf"
        sensors = list(set(sensors))
        params = {"room": room, "sensor": ",".join(sensors)}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            plot_data = response.json()
            plot_image = plot_data["bs4_img"]
            img = self.decode_base64_img(plot_image)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            iimage_file = io.BytesIO(img_byte_arr)
            return image_file
        else:
            return None

    def get_stat(self, room, sensor, tower='', shelf='', stat_type='avg'):
        DATA_ANALYSIS_HOST = sm.service_base_url("data_analysis")
        if stat_type == 'avg':
            url = f"{DATA_ANALYSIS_HOST}/average"
        else:
            url = f"{DATA_ANALYSIS_HOST}/{stat_type}"
        params = {"room": room, "sensor": sensor}
        if sensor in self.shelf_specific:
            params.update({"tower": tower, "shelf": shelf})
        response = requests.get(url, params=params)
        if response.status_code == 200:
            stat_data = response.json()
            return f"{stat_type.capitalize()} value for {self.sensors_dict[sensor]} in room {room} is {stat_data[stat_type]}"
        else:
            return f"Failed to retrieve {stat_type} value."

    def decode_base64_img(self, bs4_img):
        img = Image.open(io.BytesIO(base64.decodebytes(bytes(bs4_img, "utf-8"))))
        return img


    def save_chat_id(self, chat_id):
        try:
            with open("chat_ids.json", 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {"chats": [{"room_id": 1, "ids": []}, {"room_id": 2, "ids": []}]}

        for room in data["chats"]:
            if room["room_id"] == 1:
                room["ids"].append(chat_id)
                room["ids"] = list(set(room["ids"]))
                break

        with open('chat_ids.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        self.print_chat_ids(room_id=1)

    def print_chat_ids(self, room_id):
        try:
            with open('chat_ids.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            logging.info(f"Chat IDs for room_id {room_id}:")
            for room in data["chats"]:
                if room["room_id"] == room_id:
                    for chat_id in room["ids"]:
                        logging.info(chat_id)
                    break
            else:
                logging.info(f"No room found with room_id {room_id}.")
        except FileNotFoundError:
            logging.info("No chat IDs found.")

    def get_chat_ids(self, room_id):
        try:
            with open('chat_ids.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            for room in data["chats"]:
                if room["room_id"] == room_id:
                    return room["ids"]
            else:
                logging.info(f"No room found with room_id {room_id}.")
                return []
        except FileNotFoundError:
            logging.info("No chat IDs found.")
            return []


    def send_notification(self, params, payload):
        room_id = int(params["room"])
        chat_ids = self.get_chat_ids(room_id)
        for chat_id in chat_ids:
            self.bot.sendMessage(chat_id, payload)

        return "message forwareded to user"

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
        cherrypy.tree.mount(NotificationServ(self), '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()


    def start_rest(self, SERVICE_RNET, SERVICE_PORT):
        threading.Thread(target=self.rest_serv, kwargs={'SERVICE_RNET': SERVICE_RNET, 'SERVICE_PORT': SERVICE_PORT}).start()

