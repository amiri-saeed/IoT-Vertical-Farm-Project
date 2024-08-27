import requests
import json
import logging
import os


CATALOG_HOST = os.getenv("CATALOG_HOST", "catalog")
CATALOG_PORT = os.getenv("CATALOG_PORT", 8080)
# CATALOG_HOST = "catalog"
# CATALOG_PORT = 8080


class ServiceManager:
    def __init__(self):
        pass

    def service_registry(self, service_name, service_host, service_port):
        # send post req to catalog to be registered
        payload = {}

        payload["name"] = service_name
        payload["host"] = service_host
        payload["port"] = service_port

        url = f"http://{CATALOG_HOST}:{CATALOG_PORT}/connect"
        req = requests.post(url, json=payload)
        
        if req.status_code == 200:
            return True
        else:
            return False


    # def service_revive(self, service_name):
    #     # pings the catalog when called
    #     # should be called every x secs/minutes to indicate the service is alive...
    #     # if the service hasen't pinged catalog for less than a given time threshold, it means it is no longer alive...
    #     # upon request a service from catalog, it should check if the service is alive then return the host:port else return service is not alive
    #     url = f"http://{CATALOG_HOST}:{CATALOG_PORT}/ping?name={service_name}"
    #     req = requests.get(url)
    #     if req.status_code == 200:
    #         return "Pinged catalog."
    #     else:
    #         return False


    def service_discovery(self, service_name, room_id):
        # performs the discovery (obtaining host:port) of a service
        logging.info(service_name)
        if service_name.startswith("device_connector"):
            logging.info("discovering the device connector for the room...")
            url = f"http://{CATALOG_HOST}:{CATALOG_PORT}/all"
            req = requests.get(url)
            if req.status_code == 200:
                catalog_all = req.json()
                rooms = catalog_all["rooms"]
                for room in rooms:
                    if room_id == room["room_id"]:
                        service_name = room["device_id"]
                    else:
                        service_name == f"device_connector_{room_id[-1]}"
            else:
                logging.error(f"Error with {req.status_code}")
                host = "10.241.43.254"
                port = 8080
                return host, port


        alive = True
        url = f"http://{CATALOG_HOST}:{CATALOG_PORT}/services?name={service_name}"
        req = requests.get(url)
        
        if req.status_code == 200:
            resp = req.json() # this is a list

            if len(resp) != 0:
                host = resp[0]["host"]
                port = resp[0]["port"]
            else:
                if service_name.startswith("device_connector"):
                    host = "10.241.43.254"
                    port = 8080
                alive = False


        if alive:
            return host, port
        else:
            # return "0.0.0.0", "8080"
            return host, port

    def service_base_url(self, service_name, room_id="R1"):
        if service_name == "catalog":
            base_url = f"http://{CATALOG_HOST}:{CATALOG_PORT}"
        else:
            host, port = self.service_discovery(service_name, room_id)
            base_url = f"http://{host}:{port}"
        return base_url