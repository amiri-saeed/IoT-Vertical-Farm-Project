import cherrypy
import json
from Database import DB
from pathlib import Path
from cherrypy import HTTPError
from datetime import datetime
import schedule
import time
import logging
import threading
import requests
import sys

from Catalog import Catalog  # Assuming your class is in catalog.py

# Define a global flag to track whether the thread should exit
interrupted = False

def start_cherrypy_server():
    print("Starting the server...")
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            #'tools.sqlite.on': True  # Add this line to enable the SQLite tool
        }
    }
    catalog = Catalog()
    cherrypy.tree.mount(catalog, '/', conf)
    cherrypy.config.update({'server.socket_host': catalog.host})
    cherrypy.config.update({'server.socket_port': catalog.port})
    cherrypy.engine.start()
    cherrypy.engine.block()

def check_service_periodically(catalog_instance):
    # Define the thread object globally
    global check_service_thread
    
    def run_periodically():
        while not interrupted:  # Check the flag to gracefully exit the loop
            catalog_instance.check_microservices()
            time.sleep(120)  # Sleep for 2 minutes (120 seconds)

    # Start a separate thread to run the task periodically
    check_service_thread = threading.Thread(target=run_periodically, daemon=True)
    check_service_thread.start()

# Define a global flag to track whether the thread should exit
interrupted = False

if __name__ == "__main__":
    # Start the CherryPy server in a separate thread
    server_thread = threading.Thread(target=start_cherrypy_server)
    server_thread.daemon = True  # Daemonize the thread to allow main thread to exit
    server_thread.start()

    # Create an instance of the Catalog class
    catalog_instance = Catalog()

    # Start checking the services periodically, to see which one are still up and which one are down and needs to be cancelled from the db
    # check_service_periodically(catalog_instance)
    # non active for the sake of the tests

    try:
        # Block the main thread until CherryPy server stops
        cherrypy.engine.block()
    except KeyboardInterrupt:
        # Set the flag to True to signal the thread to exit
        interrupted = True
        # Wait for the thread to join
        check_service_thread.join()
        print("\nThread checking microservices stopped.")
        sys.exit(0)  # Exit gracefully
