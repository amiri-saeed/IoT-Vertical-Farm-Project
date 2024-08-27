import logging
import time
import json

from ts_init import ThingSpeakInit
from ts_manager import ThingSpeakManager
from mqt.ts_publisher import ExternalSubscriber
from utils.service_manager import ServiceManager


logging.basicConfig(level=logging.INFO)
SERVICE_NAME = "thingspeak_adaptor"
SERVICE_HOST = "thingspeak_adaptor"
# SERVICE_RNET = "127.0.0.1"
SERVICE_RNET = "0.0.0.0"
SERVICE_PORT = 8086


def main():

    logging.info("Registering ThingSpeak Adaptor...")
    registered = False
    sm = ServiceManager()
    while not registered:
        registered = sm.service_registry(SERVICE_NAME, SERVICE_HOST, SERVICE_PORT)
        time.sleep(3)
    logging.info("Service registered...")


    logging.info("Initializing ThingSpeak Adaptor...")
    tsi = ThingSpeakInit(fresh=True)
    tsi.update()

    logging.info("Initializing ThingSpeak Manager...")
    tsa = ThingSpeakManager(tsi)

    # Internals
    logging.info("Starting listening, translating, and speaking...")
    tsa.start_listening()
    tsa.start_translating()
    tsa.start_speaking()
    
    # REST part
    logging.info("Starting REST server...")
    tsa.start_rest(SERVICE_RNET, SERVICE_PORT)

    # MQTT tasks
    logging.info("Starting MQTT tasks...")
    broker_conf = json.load(open("ext_brokerconf.json", "r"))
    clientID = 'tsadaptor'
    broker = broker_conf["url"]
    port = broker_conf["port"]
    topic = "pub/+/+/+/#"
    external_subscriber = ExternalSubscriber(clientID, broker, port, topic, tsa)
    external_subscriber.startSim()


if __name__ == "__main__":
    main()
