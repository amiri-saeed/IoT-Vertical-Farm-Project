import json
import requests
import logging

logging.basicConfig(level=logging.INFO)



class ThingSpeakInit:
    def __init__(self, fresh):
        self.conf_path = "tsconfig.json"
        self.fresh_start = fresh
        self._read()

        self.sensors_path = "sensors.json"
        self._read_sensors()

        self.channel_op_header = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        self.binary = {"0": "11", "1": "12", "2": "21", "3": "22"}


    def config(self):
    	'''shows the content of self.conf'''
    	return self.conf

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


    def _read(self):
    	'''reads the self.path file and creates self.conf'''
    	with open(self.conf_path, "r") as in_file:
	        self.conf = json.load(in_file)


    def _write(self):
    	'''write the self.conf to self.path'''
    	with open(self.conf_path, "w") as out_file:
	    	json.dump(self.conf, out_file, indent=4)
    

    def update_channels(self, acc_key):
    	'''
		creates the updated channels list based on the account key
		since the acc key is unique for each account, using this we get channels of account
    	'''
    	for endpoint in self.conf["endpoints"]:
            if endpoint["name"] == "channel_list":
                channel_list_url = endpoint["url"].format(acc_key)
                channels = requests.get(channel_list_url).json()

    	updated_channel_list = list()
    	for channel in channels:
    		channel_struct = {
	        "id": "",
    		"write_api_key": "",
    		"read_api_key": "",
    		}
    		channel_struct["id"] = channel["id"]
    		channel_struct["write_api_key"] = channel["api_keys"][0]["api_key"]
    		channel_struct["read_api_key"] = channel["api_keys"][1]["api_key"]
    		updated_channel_list.append(channel_struct)

    	return updated_channel_list



    def clear_channels(self, acc_key):
        '''
        clear channels is basically a part of fresh start mechasim
        in fresh start we clear all the cahnnels of the account and create 4 channels

        '''
        body = {"api_key": acc_key}

        # to get current channels
        for endpoint in self.conf["endpoints"]:
            if endpoint["name"] == "channel_list":
                channel_list_url = endpoint["url"].format(acc_key)
                channels = requests.get(channel_list_url).json()

        # to clear the obtained channels
        for endpoint in self.conf["endpoints"]:
            if endpoint["name"] == "clear_channel":
                for channel in channels:
                    url = endpoint["url"].format(channel["id"])
                    logging.info(f"Clearing channel {channel['id']}...")
                    req = requests.delete(url, headers=self.channel_op_header, data=body)
                    # logging.info(req.json())

        # to trigger the create channels in next step
        if len(channels) < 4:
            return False




    def clear_channel(self, channel_id):
        '''
        clear channels is basically a part of fresh start mechasim
        in fresh start we clear all the cahnnels of the account and create 4 channels

        '''
        for account in self.conf["accounts"]:
            for channel in account["channels"]:
                if channel["id"] == channel_id:
                    acc_key = account["profile"]["user_api_key"]

        body = {"api_key": acc_key}

        # to clear the obtained channels
        for endpoint in self.conf["endpoints"]:
            if endpoint["name"] == "clear_channel":
                url = endpoint["url"].format(channel_id)
                logging.info(f"Clearing channel {channel['id']}...")
                req = requests.delete(url, headers=self.channel_op_header, data=body)
                # logging.info(req.json())




    def create_channels(self, acc_key):
        body = {
            "api_key": acc_key,
            "public_flag": True,
        }

        # [TODO] later I can write all these with function to give them the name of the
        # name of the endpoint and return the endpoint object
        # also I can do that for channels and other things
        for endpoint in self.conf["endpoints"]:
            if endpoint["name"] == "create_channel":
                for c in range(4): # only four channels per account is available
                    
                    tower_num = self.binary[f"{c}"][0]
                    shelf_num = self.binary[f"{c}"][1]
                    body["name"] = "R1/T{}/S{}".format(tower_num, shelf_num)
                    
                    for field in range(7):
                        body[f"field{field+1}"] = self.fixed_sens[field]
                    body["field8"] = self.unfixed_sens[c]

                    url = endpoint["url"]
                    req = requests.post(url, headers=self.channel_op_header, data=body)
                    logging.info(req.json())
                    logging.info(body)




    def update(self, write=True):
        '''
		for now it updates channels of accounts, other update methods can be added
		(currently no method to update devices)
        '''

        # This part updates the credential and such for channels based on the given account
        for account in self.conf["accounts"]:
            acc_key = account["profile"]["user_api_key"]
            # in fresh start we check if we have channels and clear them
            # else we create 4 channels
            if self.fresh_start:
                logging.info("Clearing and Creating channels...")
                channels_exist = self.clear_channels(acc_key)
                if channels_exist:
                    self.create_channels(acc_key)

            account["channels"] = self.update_channels(acc_key)

        # This writes the current channels creds to config file
        if write:
            self._write()
