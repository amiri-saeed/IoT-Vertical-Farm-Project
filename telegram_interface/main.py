import json
import time
from telbot import *
from rest import rest_serv
import logging
from utils.service_manager import ServiceManager


logging.basicConfig(level=logging.INFO)


SERVICE_NAME = "telegram_interface"
SERVICE_HOST = "telegram_interface"
SERVICE_PORT = 8089
SERVICE_RNET = "0.0.0.0"
# SERVICE_RNET = "127.0.0.1"



def main():
    conf = json.load(open("bot_conf.json", 'r'))
    token = conf["TOKEN"]

    bot = SmartGardenBot(token)
    bot.rest_serv(SERVICE_RNET, SERVICE_PORT)


if __name__ == "__main__":
    logging.info("Registering Telegram Interface...")
    registered = False
    sm = ServiceManager()
    while not registered:
        registered = sm.service_registry(SERVICE_NAME, SERVICE_HOST, SERVICE_PORT)
        time.sleep(3)
    logging.info("Service registered...")

    logging.info("Initiating Telegram Interface...")
    main()