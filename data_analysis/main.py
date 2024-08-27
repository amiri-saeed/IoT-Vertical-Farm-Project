import logging
import time
from data_analysis import DataAnalysis
from utils.service_manager import ServiceManager


logging.basicConfig(level=logging.INFO)


SERVICE_NAME = "data_analysis"
SERVICE_HOST = "data_analysis"
SERVICE_PORT = 8085
SERVICE_RNET = "0.0.0.0"
# SERVICE_RNET = "127.0.0.1"



def main():

    analyzer = DataAnalysis()
    analyzer.start_rest(SERVICE_RNET, SERVICE_PORT)


if __name__ == "__main__":
    
    logging.info("Registering Data Analysis...")
    registered = False
    sm = ServiceManager()
    while not registered:
        registered = sm.service_registry(SERVICE_NAME, SERVICE_HOST, SERVICE_PORT)
        time.sleep(3)
    logging.info("Service registered...")

    logging.info("Initiating Analysis Server...")
    main()