import logging
import time
from light_manager import *


logging.basicConfig(level=logging.INFO)
SERVICE_NAME = "light_management"
SERVICE_HOST = "light_management"
# SERVICE_RNET = "127.0.0.1"
SERVICE_RNET = "0.0.0.0"
SERVICE_PORT = 8082


def main():

    logging.info("Performing tasks...")
    sensor_retriever = SensorDataRetriever()
    catalog = CatalogIntegration()

    catalog_data = catalog.fetch_plant_info()
    farm, optimal_values_map = Farm.initialize_from_catalog(catalog_data)

    processed_data = DataProcessor.process_sensor_data(farm, sensor_retriever, optimal_values_map)

    notifier = Notifier()
    notifier.tasks(processed_data)


if __name__ == "__main__":
        
    logging.info("Registering Light Management...")
    registered = False
    sm = ServiceManager()
    while not registered:
        registered = sm.service_registry(SERVICE_NAME, SERVICE_HOST, SERVICE_PORT)
        time.sleep(3)
    logging.info("Service registered...")

    server = Serv()
    server.start_rest(SERVICE_RNET, SERVICE_PORT)

    # for this manager, checking every 30 minutes would be sufficient.
    minutes = 30  # Checking every 30 minutes
    logging.info("Sleep for rasp to register and values come in...")
    init_sleep = 10
    time.sleep(init_sleep * 60)

    while True:
        try:
            main()
            logging.info(f"Performed Light Management Tasks, sleeping for {minutes} minutes...")
            time.sleep(minutes * 60)
        except Exception as e:
            logging.info("Error occurred during Light Management tasks.")
            logging.info(str(e))

        time.sleep(30)
