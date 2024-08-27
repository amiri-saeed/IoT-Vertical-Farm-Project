import logging
import time
from nutrient_manager import *


logging.basicConfig(level=logging.INFO)
SERVICE_NAME = "nutrient_dosing_management"
SERVICE_HOST = "nutrient_dosing_management"
# SERVICE_RNET = "127.0.0.1"
SERVICE_RNET = "0.0.0.0"
SERVICE_PORT = 8081


def main():

    logging.info("Performing tasks...")
    sensor_retriever = SensorDataRetriever()
    catalog = CatalogIntegration()
    
    catalog_data = catalog.fetch_plant_info()
    farm, optimal_values_map = Farm.initialize_from_catalog(catalog_data)
    processed_data = DataProcessor.process_sensor_data(farm, sensor_retriever, optimal_values_map)
    
    # in the scope of nutrient management we only notify user 
    notifier = UserNotifier()
    notifier.notify_users(processed_data)

if __name__ == "__main__":
    
    logging.info("Registering Nutrient Dosing Management...")
    registered = False
    sm = ServiceManager()
    while not registered:
        registered = sm.service_registry(SERVICE_NAME, SERVICE_HOST, SERVICE_PORT)
        time.sleep(3)
    logging.info("Service registered...")

    server = Serv()
    server.start_rest(SERVICE_RNET, SERVICE_PORT)

    # for this manager, checking every 3 hours would be sufficient.
    hours = 1
    logging.info("sleep for rasp to register and values come in...")
    init_sleep = 10
    time.sleep(init_sleep*60)

    while True:
        try:
            main()
            logging.info(f"\nPerformed Nutrient Management Tasks, sleep for {hours} hours...")
            time.sleep(hours*60*60)
        except Exception as e:
            logging.info("Error occurred during Nutrient Dosing Management tasks.")
            logging.info(str(e))

        time.sleep(5)
