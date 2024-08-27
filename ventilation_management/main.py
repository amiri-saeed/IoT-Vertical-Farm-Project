import logging
import time
from ventilation_manager import *


logging.basicConfig(level=logging.INFO)
SERVICE_NAME = "ventilation_management"
SERVICE_HOST = "ventilation_management"
# SERVICE_RNET = "127.0.0.1"
SERVICE_RNET = "0.0.0.0"
SERVICE_PORT = 8084


def main():

    logging.info("Performing tasks...")
    sensor_retriever = SensorDataRetriever()
    catalog = CatalogIntegration()

    catalog_data = catalog.fetch_plant_info()
    # print(catalog_data)
    farm, optimal_values_map = Farm.initialize_from_catalog(catalog_data)

    processor = DataProcessor()
    processed_data, room_processed_data = processor.process_sensor_data(farm, sensor_retriever, optimal_values_map)

    # in the scope of ventilation management we notify user, activate the ventilation in the room and update the catalog
    notifier = Notifier()
    notifier.tasks(processed_data, room_processed_data)


if __name__ == "__main__":

    logging.info("Registering Ventilation Management...")
    registered = False
    sm = ServiceManager()
    while not registered:
        registered = sm.service_registry(SERVICE_NAME, SERVICE_HOST, SERVICE_PORT)
        time.sleep(3)
    logging.info("Service registered...")

    server = Serv()
    server.start_rest(SERVICE_RNET, SERVICE_PORT)

    # for this manager, checking every 15 minutes would be sufficient since
    minutes = 15
    logging.info("sleep for rasp to register and values come in...")
    init_sleep = 10
    time.sleep(init_sleep*60)
    while True:
        try:
            main()
            logging.info(f"Performed Ventilation Management Tasks, sleep for {minutes} minutes...")
            time.sleep(minutes*60)
            
        except Exception as e:
            logging.info("Error occurred during Venetilation Management tasks.")
            logging.info(str(e))

        time.sleep(30)