import json
import time
import datetime
import queue
import threading
from threading import Thread
import logging

import requests

import cherrypy
from rest.server import WebServ

from mqt.ts_publisher import TSPublisher


logging.basicConfig(level=logging.INFO)




class ThingSpeakManager:

	def __init__(self, tsi):
		self.sensors_path = "sensors.json"
		self.tsi = tsi
		self.conf = tsi.config()
		self.acc_ids = [account["id"] for account in self.conf["accounts"]]
		
		self._read_sensors()
		self._init_tspub()
		self._init_tsreq()

		self.write_free = False
		self.req_sleep = 10

		self.external_payload_queue = queue.Queue()
		self.unified_source_queue = queue.Queue()
		self.unified_output_queue = queue.Queue()

		self.external_payload_lock = threading.Lock()
		self.unified_source_lock = threading.Lock()
		self.unified_output_lock = threading.Lock()

		self.sensor_mapping = {
		    "temperature": "temp",
		    "CO2 level": "co2",
		    "Nitrogen": "n",
		    "Phosphorus": "k",
		    "Potassium": "p",
		    "HC-SR04": "height",
		    "humidity": "humid",
		    "temp": "temp",
		    "co2": "co2",
			"humid": "humid",
		    "water": "water",
		    "height": "height",
		    "li": "li",
		    "pH": "ph",
		    "n": "n",
		    "k": "k",
			"p": "p",
			"moisture": "moisture",
		}



	def _init_tspub(self):
		client_id = self.conf["accounts"][0]["devices"][0]['client_id']
		username = self.conf["accounts"][0]["devices"][0]['username']
		password = self.conf["accounts"][0]["devices"][0]['password']
		broker = self.conf['broker']
		port = int(self.conf['port'])
		self.tsp = TSPublisher(client_id, username, password, broker, port)


	def _init_tsreq(self):
		self.ts_write_header = {
		    "Content-Type": "application/json",
		    "Accept": "application/json"
		}
		


	def _read_sensors(self):
		# for sensors we have to preserve this structure and order
		# regardless of channel/account/any new changes
		'''
		{
		  "fixed": ["ph", "moisture", "n", "p", "k", "height", "li"],
		  "unfixed": ["temp", "humid", "co2", "water"]
		}
		'''
		with open(self.sensors_path, "r") as f:
			sensors = json.load(f)
			self.fixed_sens = sensors["fixed"]
			self.unfixed_sens = sensors["unfixed"]


	def read_account(self, account_id=1):
		for account in self.conf["accounts"]:
			if account["id"] == account_id:
				return account
			else:
				return f"No account with id: {account_id} was found."


	def read_channel_keys(self, channel_id, account_id=1):
		account = self.read_account(account_id)
		for channel in account["channels"]:
			if channel["id"] == channel_id:
				return channel


	def read_channel_feed(self, channel_id):
		for endpoint in self.conf["endpoints"]:
			if endpoint["name"] == "channel_feed":
				channel_keys = self.read_channel_keys(channel_id)
				if channel_keys is not None:
					url = endpoint["url"].format(channel_id, channel_keys["read_api_key"])
					channel = requests.get(url).json()
					return channel

	
	# WORKS
	def _channel_id(self, channel_num):
		'''
	    Retrieve the channel ID based on the channel number.
	    
	    Arguments:
	        channel_num (int): The channel number, should be in [1, 2, 3, 4].
	        
	    Returns:
	        int: The channel ID corresponding to the given channel number.
	    '''
	    # Obtain all channel IDs, sort them, and assign channel numbers.
	    # [TODO] ADD SUPPORT FOR ACC NUMBER FOR OTHER ROOM/USERS, HAVE TO ONLY ADD ARGUMENT IN read_account() 
		channels = self.read_account()["channels"]
		ids = sorted([int(channel["id"]) for channel in channels])
		return ids[channel_num-1]


	# WORKS
	def _ext_binary_log(self, first_num, second_num):
	    '''
	    Determine the channel ID based on tower and shelf numbers.
	    
	    Arguments:
	        first_num (int): The tower number (0 or 1).
	        second_num (int): The shelf number (0 or 1).
	        
	    Returns:
	        int: The channel ID to write to.
	    '''
	    if int(first_num) > 2 or int(second_num) > 2:
	    	# logging.info("Incorrect Tower or Shelf Number.")
	    	return None
	    else:
		    fn = int(first_num) - 1 #in [0, 1]
		    sn = int(second_num) - 1 #in [0, 1]
		    channel_num = int(f"{fn}{sn}", 2) + 1 #out [1, 2, 3, 4]
		    channel_id = self._channel_id(channel_num)
	    return channel_id


	# WORKS
	def source(self, topic, sensor_name):
		'''
	    Translate MQTT topic and sensor name to a ThingSpeak field notation.
	    
	    Arguments:
	        topic (str): MQTT topic of the form 'pub/room{}/tower{}/shelf{}'.
	        sensor_name (str): Name of the sensor.
	        
	    Returns:
	        str: ThingSpeak notation representing the sensor's field.
	    '''
		rts = topic.split('/')
		print(rts)
		room_num = rts[1][::-1][0] # would indicate the account to write to
		tower_num = rts[2][::-1][0] # this and shelf_num would indicate the cahnnel to write to
		shelf_num = rts[3][::-1][0]
		field_num  = sensor_name
		if sensor_name in self.fixed_sens:
			field_num = self.fixed_sens.index(sensor_name)
		else:
			# the shared sensor in the room which is stored always at field8
			field_num = sensor_name
		# _source = f"{rts}/{sensor_name}"
		# return _source
		return f"{room_num}/{tower_num}/{shelf_num}/{field_num}"


	# WORKS
	def translate_to_topic(self, source):
	    '''
	    Translate source notation to the MQTT topic format for publishing.
	    
	    Arguments:
	        source (str): ThingSpeak notation representing the sensor's field.
	        
	    Returns:
	        str: MQTT topic format for publishing.
	    '''
	    source_parse = source.split('/')
	    if source_parse[-1] in self.unfixed_sens:
	    	sensor_name = source_parse[-1]
	    	channel_num = int(self.unfixed_sens.index(sensor_name)) + 1
	    	channel_id = self._channel_id(channel_num)
	    	field_num = 8
	    else:
	    	room_num = source_parse[0] # to be used somehow, currently not being used
	    	tower_num = source_parse[1]
	    	shelf_num = source_parse[2]
	    	field_num = str(int(source_parse[3]) + 1)
	    	channel_id = self._ext_binary_log(tower_num, shelf_num)

	    return f"channels/{channel_id}/publish/fields/field{field_num}"



	# WORKS
	def end_to_end_translation_topic(self, topic, sensor_name):
		'''
	    Translate an external MQTT topic and sensor name to a ThingSpeak MQTT topic format.

	    Args:
	        topic (str): The external MQTT topic.
	        sensor_name (str): The name of the sensor.

	    Returns:
	        str: The translated ThingSpeak MQTT topic.

	    Examples:
	        end_to_end_translation_topic("pub/room1/tower2/shelf1", "ph")
	        Output: 'channels/2462864/publish/fields/1'
	        end_to_end_translation_topic("pub/room1/tower2/shelf2", "water")
	        Output: 'channels/2462864/publish/fields/8'
	    '''
		_source = self.source(topic, sensor_name)
		return self.translate_to_topic(_source)


	def event_parse(self, event):
	    '''
	    Parse data from a single event.

	    Args:
	        event (dict): The event dictionary containing sensor data.

	    Returns:
	        str: A string representing the parsed event data.

	    Example:
	        event_parse({"n": "k", "u": "kg/ha", "v": 180})
	        Output: 'k/180'
	    '''
	    # print("name before mapping", event["n"])
	    sens_name = self.sensor_mapping[event["n"]]
	    print("name after mapping", sens_name)
	    sens_valu = event["v"]

	    # to be figured out
	    parsed_event = f"{sens_name}/{sens_valu}"
	    return parsed_event

	def payload_parse(self, payload):
        # payloads published to external broker can be of two forms:
        #     single event payloads (with one sen/val pair)
        #     multiple event payloads (with multiple sen/val pairs)
        # should output bulk regardless of single/multiple input
        # bulk input to middle processes should be handled there

	    bulk_events = []
	    structures = [] # of form topic-event
	    events = payload["e"]
	    
	    for event in events:
	        parsed_event = self.event_parse(event)
	        bulk_events.append(parsed_event)

	    return bulk_events



	def listen(self):
	    while True:
	        try:
	            with self.external_payload_lock:
	                if not self.external_payload_queue.empty():  # Check if queue is not empty
	                    topic, payload = self.external_payload_queue.get()  # Blocking call

	                    self.external_payload_queue.task_done()  # Move task_done inside the lock
	                else:
	                    continue  # Skip iteration if queue is empty

	            # print("typeeeeee", type(payload))
	            # Directly use the payload as it is already a dictionary
	            unified_source = self.listen_behavior(topic.replace("-", ""), payload)
	            logging.info(unified_source)

	            with self.unified_source_lock:
	                self.unified_source_queue.put(unified_source)

	        except Exception as e:
	            logging.error(f"Error in listen method: {e}")
	            # Optional: Add a sleep to avoid a tight loop in case of continuous errors
	            time.sleep(1)



	
	def listen_behavior(self, topic, payload):
		unified_source = list()
		for event in self.payload_parse(payload):
			unified_source.append(f"{topic}-{event}")
			logging.info(f"the source .... {topic}-{event}")
		return unified_source


	def unified_translations(self):
		while True:
		    with self.unified_source_lock:
		        if not self.unified_source_queue.empty():
		            unified_source = self.unified_source_queue.get()
		            self.unified_source_queue.task_done()
		        else:
		            continue

		    unified_out = self.translate_behavior(unified_source)

		    with self.unified_output_lock:
		        self.unified_output_queue.put(unified_out)

	def translate_behavior(self, unified_sources):
		unified_out = list()
		for source in unified_sources:
			source = source.split('-')
			topic = source[0]
			sens_name = source[1].split('/')[0]
			value = source[1].split('/')[1]
			destination = self.end_to_end_translation_topic(topic, sens_name)
			unified_out.append(f"{destination}-{value}")
		return unified_out

	def separate_by_channel(self, data):
		'''to get different channel write reqs seperated'''
		channel_data = {}

		for item in data:
			channel_id = item.split('/')[1]

			if channel_id not in channel_data:
				channel_data[channel_id] = [item]
			else:
				channel_data[channel_id].append(item)

		result = [v for _, v in channel_data.items()]
		return result

	def speak(self):
	    while True:
	        with self.unified_output_lock:
	            if not self.unified_output_queue.empty():
	                unified_out = self.unified_output_queue.get()
	                self.unified_output_queue.task_done()
	            else:
	                continue

	        self.speak_behavior(unified_out)


	def speak_behavior(self, unified_out):
		'''
		e.g. of unified resource: 'channels/2462865/publish/fields/field4-21'
		'''

		# # MQTT
		# # NOT GOING TO BE USED ANYMORE...
		# logging.info("start publishing to TSP...")
		# self.tsp.startSim()
		# for ufs in unified_out:
		#     top = ufs.split('-')[0]
		#     val = int(ufs.split('-')[1])
		#     logging.info(f"publishing to {top} val {val}")
		#     self.tsp.publish(top, int(val))
		#     time.sleep(3)
		# self.tsp.stopSim()
		
		# REST
		logging.info(f"created payload at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		unified_outs = self.separate_by_channel(unified_out)
		logging.info(unified_outs)
		for unified_out in unified_outs:
			body = {
				"write_api_key": None,
				"updates": [{
					"created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					}
				]
			}
			for ufs in unified_out:
				
				channel_field = ufs.split('-')[0].split('/')
				# print(channel_field)

				# to fill the url and get write api key
				channel_id = channel_field[1]

				# to fill the body
				field = channel_field[-1] 
				val = float(ufs.split('-')[1])
				body["updates"][0][field] = val

			body["write_api_key"] = self.read_channel_keys(int(channel_id))["write_api_key"]
			for endpoint in self.conf["endpoints"]:
				if endpoint["name"] == "bulk_write":
					url = endpoint["url"].format(channel_id)
					req = requests.post(url, headers=self.ts_write_header, data=json.dumps(body))
					logging.info(f"{body['updates']}")
					time.sleep(self.req_sleep)




	def add_external_payload(self, topic, payload):
	    with self.external_payload_lock:
	        print("payload", payload)
	        # print("type payload", type(payload))
	        # Ensure payload is a dictionary before putting it in the queue
	        if not isinstance(payload, dict):
	            raise ValueError("Payload must be a dictionary")
	        self.external_payload_queue.put((topic, payload))


	def start_listening(self):
	    listen_thread = threading.Thread(target=self.listen)
	    listen_thread.start()

	def start_translating(self):
	    translate_thread = threading.Thread(target=self.unified_translations)
	    translate_thread.start()

	def start_speaking(self):
	    speak_thread = threading.Thread(target=self.speak)
	    speak_thread.start()





	# methods for REST
	# def translate_params_retrieve(self, param):
	# 	'''
	# 	Would translate the endpoint params
	# 	to suitable TSP channel/field values to be passed to retrieve data
	# 	'''

	# 	# parsing required params
	# 	room_num = param["room"] # would be used for other users/accounts later
	# 	if "tower" in param.keys() and "shelf" in param.keys():
	# 		tower_num = param["tower"]
	# 		shelf_num = param["shelf"]
	# 	sensor = param["sensor"]

	# 	# checking for optional params
	# 	if "last" in param.keys():
	# 		results = param["last"]
	# 	else:
	# 		results = 25

	# 	if "start" in param.keys():
	# 		start_time = param["start"]
	# 	else:
	# 		start_time = datetime.datetime(1970, 1, 1).strftime('%Y-%m-%d %H:%M:%S') # default time, a long time ago

	# 	if "end" in param.keys():
	# 		end_time = param["end"]
	# 	else:
	# 		end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # default current time, to get the most recent entries

	# 	if sensor in self.unfixed_sens:
	# 		# parse for room/tower/shelf
	# 		channel_num = int(self.unfixed_sens.index(sensor)) + 1
	# 		channel_id = self._channel_id(channel_num)
	# 		field_num = 8

	# 	if sensor in self.fixed_sens:
	# 		# get the account for the room
	# 		channel_id = self._ext_binary_log(tower_num, shelf_num)
	# 		field_num = self.fixed_sens.index(sensor) + 1

	# 	translated = {
	# 			"required": {
	# 				"channel_id": channel_id,
	# 				"field_num": field_num
	# 			},
	# 			"optional": {
	# 				"results": results,
	# 				"start": start_time,
	# 				"end": end_time
	# 			}
	# 	}

	# 	return translated
	
	def translate_params_retrieve(self, param):
	    '''
	    Translate the endpoint params to suitable TSP channel/field values to be passed to retrieve data.
	    '''

	    # Default values and required parameters
	    room_num = param.get("room")  # Extract room number; assume it's required

	    # Optional parameters
	    tower_num = param.get("tower")  # Extract tower number if present
	    shelf_num = param.get("shelf")  # Extract shelf number if present
	    sensor = param.get("sensor")  # Extract sensor; assume it's required

	    results = param.get("last", 25)  # Default to 25 if 'last' not provided

	    start_time = param.get("start", datetime.datetime(1970, 1, 1).strftime('%Y-%m-%d %H:%M:%S'))
	    end_time = param.get("end", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

	    # Initialize variables
	    channel_id = None
	    field_num = None

	    if sensor in self.unfixed_sens:
	        # Parse for room/tower/shelf
	        channel_num = int(self.unfixed_sens.index(sensor)) + 1
	        channel_id = self._channel_id(channel_num)
	        field_num = 8

	    elif sensor in self.fixed_sens:
	        # Get the account for the room
	        if tower_num is None or shelf_num is None:
	            raise ValueError("Tower and shelf numbers must be provided for fixed sensors")
	        channel_id = self._ext_binary_log(tower_num, shelf_num)
	        field_num = self.fixed_sens.index(sensor) + 1

	    if channel_id is None or field_num is None:
	        raise ValueError("Sensor type not recognized or missing channel_id/field_num")

	    translated = {
	        "required": {
	            "channel_id": channel_id,
	            "field_num": field_num
	        },
	        "optional": {
	            "results": results,
	            "start": start_time,
	            "end": end_time
	        }
	    }

	    return translated




	def translate_params_clear(self, param):
		'''
		Would translate the endpoint params
		to suitable TSP channel/field values to be passed to retrieve data
		'''

		if "room" not in param.keys():
			translated = "Room is not specified."

		else:
			'''if the room is correctly specified'''
			if "tower" in param.keys() and "shelf" in param.keys():
				'''the case of correct room/tower/shelf'''
				room_num = param["room"]
				tower_num = param["tower"]
				shelf_num = param["shelf"]

				channel_id = self._ext_binary_log(tower_num, shelf_num)
				if channel_id != None:
					'''
					this part clears a channel
					since some of the sensors are shared in the room
					we have to reupload the values for them after clearing the channel
					we can retrieve data, reformat it
					after clearing the channel we can upload it
					'''

					def thread_submit():
						channel_eight_data = self.ret_channel_field_eight(channel_id)
						self.tsi.clear_channel(channel_id)
						if len(channel_eight_data) > 0:

							while True:
								try:
									resp = self.sub_channel_field_eight(channel_id, channel_eight_data)
									time.sleep(0.5)
									if resp.json()["success"]:
										logging.info("successfully submitted...")
										break
									else:
										logging.info("waiting for 5...")
										time.sleep(5)
								except Exception as e:
									logging.info(str(e))

					thread = threading.Thread(target=thread_submit)
					thread.start()
					thread.join()


					translated = f"shelf {shelf_num} of tower {tower_num} cleared."
				else:
					translated = "non-valid numbers."
				

			# elif ("tower" in param.keys() and "shelf" not in param.keys()) or ("tower" not in param.keys() and "shelf" in param.keys()):
			elif ("tower" in param.keys()) ^ ("shelf" in param.keys()):
				'''the case of not specifiying either tower or shelf'''
				translated = "Tower and Room must both be specified."

			else:
				'''the case of only specifying the room'''
				for account in self.conf["accounts"]:
					if account["id"] == int(param["room"]):
						acc_key = account["profile"]["user_api_key"]
					else:
						translated = "No user assigned to this room."

				def thread_clear():
					self.tsi.clear_channels(acc_key)
				thread = threading.Thread(target=thread_clear)
				thread.start()
				thread.join()

				translated = f"room {param['room']} cleared."
 
		return translated



	def ret_channel_field_eight(self, channel_id):
		for endpoint in self.conf["endpoints"]:
			if endpoint["name"] == "read_data":
				num_res = 8000 # maximum possible number of results to be retrieved
				start_time = datetime.datetime(1970, 1, 1).strftime('%Y-%m-%d %H:%M:%S')
				end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				url = endpoint["url"].format(channel_id, str(8), num_res, start_time, end_time)
				req = requests.get(str(url)).json()["feeds"]
		logging.info(f"field 8 of channel {channel_id} retrieved...")
		return req


	def sub_channel_field_eight(self, channel_id, old_data):
		body = {
			"write_api_key": self.read_channel_keys(int(channel_id))["write_api_key"],
			"updates": None,
		}
		headers = {
		    "Content-Type": "application/json",
		    "Accept": "application/json"
		}
		updates = []
		for entry in old_data:
			if entry["field8"] is not None:
			    formatted_entry = {
			        "created_at": entry["created_at"].replace('T', ' ').replace('Z', ''),
			        "field8": entry["field8"]
			    }
			    updates.append(formatted_entry)

		# [NOTE]
		# in the case we have more than 960 values
		# ThingSpeak can't take more than 960 values at once
		# so let's keep the last 960 updates for now
		# later if more values needed to be kept some new
		# uploading strategy would be adopted
		if len(updates) > 960:
		    updates = updates[-960:]
		body["updates"] = updates
		logging.info(body)

		# for endpoint in self.conf["endpoints"]:
		# 	if endpoint["name"] == "bulk_write":
		# 		url = endpoint["url"].format(channel_id)
		# 		logging.info(self.write_free)
		# 		req = requests.post(url, headers=headers, data=json.dumps(body))
		# 		logging.info(req.json())
		# 		logging.info(f"reuploaded old data of field 8 of channel {channel_id}")

		for endpoint in self.conf["endpoints"]:
			if endpoint["name"] == "bulk_write":
				url = endpoint["url"].format(channel_id)
				req = requests.post(url, headers=headers, data=json.dumps(body))
		return req
				



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
	    cherrypy.tree.mount(WebServ(self), '/', conf)
	    cherrypy.engine.start()
	    cherrypy.engine.block()


	def start_rest(self, SERVICE_RNET, SERVICE_PORT):
		threading.Thread(target=self.rest_serv, kwargs={'SERVICE_RNET': SERVICE_RNET, 'SERVICE_PORT': SERVICE_PORT}).start()
