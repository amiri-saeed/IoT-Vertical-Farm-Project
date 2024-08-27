import cherrypy
import json
from database import DB
from pathlib import Path
from cherrypy import HTTPError
from datetime import datetime
import schedule
import time
import logging
import threading
import requests
import sys

class Catalog(object):
    exposed = True

    def __init__(self):
        # read Catalog configuration
        config = json.load(open("config_catalog.json"))
        self.host = config['host']
        self.port = int(config['port'])
        self.db_name = "catalog.db"
        if not Path(self.db_name).is_file(): # see if catalog.db exists
            print("Database file not found. Creating a new empty database file.")
            Path(self.db_name).touch() # create file
            self.create_tables() # create the tables on the DB if they don't already exist


    def GET(self,*uri,**params): # uri is CASE SENSITIVE
        # Each method may handle requests from different clients concurrently, and 
        # using separate instances of the database connection ensures that 
        # each request is processed independently without interfering with others.

        db = DB(self.db_name)  # Create a new DB instance
        
        try:
            # GET host/shelves/room_id/tower_id/shelf_id
            # IMPORTANT pass '#' as %23 or else it would not work
            if uri and len(uri) > 2 and len(uri) < 5 and uri[0] == "shelves":
                room_id = uri[1]
                if uri[2] == '*' and len(uri) == 3:         # /shelves/room_id/*
                    tower_id = None
                    shelf_id = None
                    cond = {'room_id': room_id}
                elif uri[2] == '#': 
                    if len(uri) == 4:
                        if uri[3] == '*' or uri[3] == '#':  # /shelves/room_id/#/* or /shelves/room_id/#/#
                            tower_id = None
                            shelf_id = None
                            cond = {'room_id': room_id}
                        else:                               # /shelves/room_id/#/shelf_id
                            shelf_id = uri[3]
                            tower_id = None
                            cond = {'room_id': room_id, 'shelf_id': shelf_id}
                    else:
                        raise HTTPError(400, "Invalid URI format. Please provide the URI in the format 'shelves/{room_id}/{tower_id}/{shelf_id}'.")
                elif len(uri) > 3 and uri[2].startswith("T"):
                    tower_id = uri[2]
                    if uri[3] == '*' or uri[3] == '#':      # /shelves/room_id/tower_id/* or /shelves/room_id/tower_id/#
                        shelf_id = None
                        cond = {'room_id': room_id, 'tower_id' : tower_id}
                    elif uri[3].startswith("S"):            # /shelves/room_id/tower_id/shelf_id
                        shelf_id = uri[3]
                        cond = {'room_id': room_id, 'tower_id' : tower_id, 'shelf_id' : shelf_id}
                    else:
                        raise HTTPError(400, "Bad Request: Invalid URI")
                else:
                    raise HTTPError(400, "Bad Request: Invalid URI")
                
                shelf_data = db.fetch_dict("shelves", cond)

                if shelf_data:
                    plant_ids = db.search_all_values("shelves", cond, column_name='plant_id')
                    combined_data = []
                    i = 0
                    for plant_id in plant_ids:
                        plant_info = db.fetch_dict("plants", condition={'plant_id': plant_id})
                        if plant_info:
                            sd = shelf_data[i]
                            pd = plant_info[0] 
                            combined_data.append({
                                "room_id": sd['room_id'],
                                "tower_id": sd['tower_id'],
                                "shelf_id": sd['shelf_id'],
                                "plant_id": sd['plant_id'],
                                "plant_name": pd['plant_name'],
                                "plant_type": pd['type_id'],
                                "status": sd['status'],
                                "light": sd['light'],
                                "status_light": sd['status_light'],
                                "water_pump": sd['water_pump']
                            })
                        else:
                            raise HTTPError(404, "No plant information found")
                        i = i+1 # to iterate on the found data
                    if combined_data:
                        return json.dumps(combined_data, indent=4)  # Return combined data as JSON
                    else:
                        raise HTTPError(404, "Invalid URI or no information found for the specified location")
                else:
                    raise HTTPError(404, "Invalid URI or no information found for the specified location")
            
            # GET /table_name[?key1=...]
            elif uri and uri[0] in db.tables():
                table_name = uri[0]

                conditions = {}
                for key, value in params.items():
                    conditions[key] = value
                table_data = db.fetch_dict(table_name, conditions)
                # Return the JSON response with everything found
                return  json.dumps(table_data, indent = 4)
            
            # GET host/all
            elif uri and uri[0] == "all": # fetch data from the whole database
                ret = db.export_json_all()
                return ret
            
            else: 
                raise HTTPError(404, "Page not found")
            
        except HTTPError as e:  # Catch HTTPError and return as is
            raise
        except Exception as e:
            # Log the exception
            cherrypy.log(str(e))
            # generic error message
            raise HTTPError(500, f"Internal Server error {e}")
        finally:
            db.close()

    def POST(self,*uri,**params): # POST method for creating new resources or updating old ones
        db = DB(self.db_name)
        try:
            # /prefill
            if uri and uri[0] == "prefill":
                self.prefill_database()
                exp = db.export_json_all()
                print("The database has been filled with sample values. Topics and services were also deleted!.")
                return exp
            # /connect
            elif uri and uri[0] == "connect":
                try:
                    # Read and decode the JSON data from the request body
                    data = cherrypy.request.body.read().decode('utf-8')
                    # Parse the JSON data
                    data = json.loads(data)
                    # Extract device_id and sensors from the parsed JSON data
                    
                    service_name = data.get("name")                    
                    device_id = data.get("device_id")
                    
                    if device_id:
                        sensors = data.get("sensors")
                        actuators = data.get("actuators")
                        response_data = []                        
                        
                        for sensor in sensors:
                            room_id = sensor.get("room_id")
                            tower_id = sensor.get("tower_id")
                            shelf_id = sensor.get("shelf_id")
                            sensor_id = sensor.get("sensor_id")  
                            topic = f"pub/{room_id}/{tower_id}/{shelf_id}"
                            response_data.append({"sensor_id": sensor_id, "topic": topic})
                        
                            existing_rooms = db.fetch_dict("rooms", condition={"room_id": room_id})
                            if existing_rooms: # the room_id is present in the db
                                existing_room = existing_rooms[0]
                                existing_device_id = existing_room["device_id"]
                                print(f"existing_device_id: {existing_device_id}, new device_id : {device_id}")
                                if existing_device_id == "" or existing_device_id == device_id:
                                    # Update device_id for the existing room
                                    db.update("rooms", {'condition': {'room_id': room_id}, 'new_data': {'device_id': device_id}})                                
                                else:
                                    # Another device is already associated with this room
                                    raise HTTPError(409, f"The device {existing_device_id} is already associated with room {room_id}.")
                            else:
                                # Insert a new room with device_id, creates a new room
                                db.insert("rooms", (room_id, device_id, 'OFF'))
                                print(f"insert {topic}")
                            
                            # Check if the sensor already exists for this device
                            existing_sensors = db.fetch("topics", condition={'device_id': device_id})
                            if not any(sensor[0] == sensor_id for sensor in existing_sensors):
                                # Insert a new sensor for this device
                                db.insert("topics", (sensor_id, device_id, topic))
                            
                        # Prepare response JSON
                        response = {"topics_to_publish": response_data}

                        for actuator in actuators:
                            actuator_id = actuator.get("actuator_id")
                            room_id = actuator.get("room_id")
                            # ventilation
                            if actuator_id.startswith("ventilation"):
                                db.update("rooms", {'condition': {'room_id': room_id}, 'new_data': {'ventilation_id': actuator_id}})
                            else:
                                tower_id = actuator.get("tower_id")
                                shelf_id = actuator.get("shelf_id")
                                # light
                                if actuator_id.startswith("light"):
                                    db.update("shelves", {'condition': {'room_id': room_id, 'tower_id': tower_id, 'shelf_id': shelf_id}, 'new_data': {'light_id': actuator_id}})
                                # status light
                                elif actuator_id.startswith("status_light"):
                                    db.update("shelves", {'condition': {'room_id': room_id, 'tower_id': tower_id, 'shelf_id': shelf_id}, 'new_data': {'status_light_id': actuator_id}})
                                # water pump
                                elif actuator_id.startswith("water_pump"):
                                    db.update("shelves", {'condition': {'room_id': room_id, 'tower_id': tower_id, 'shelf_id': shelf_id}, 'new_data': {'water_pump_id': actuator_id}})
                    elif service_name:
                        table_name = "services"
                        service_names = [
                            "nutrient_dosing_management",
                            "light_management",
                            "water_management",
                            "ventilation_management",
                            "data_analysis",
                            "thingspeak_adaptor",
                            "user_interface",
                            "telegram_interface"
                        ]
                        if service_name in service_names or service_name.startswith("device_connector"):
                            host = data.get("host")
                            port = data.get("port")
                            if host and port:
                                # Check if service exists
                                existing_service = db.fetch_dict(table_name, condition={"name": service_name})
                                # If service exists and data has changed, update it including last_updated
                                if existing_service:
                                    db.update(table_name, {'condition': {'name': service_name},'new_data': {'host': host, 'port': port, 'last_updated': datetime.now()}})
                                # If service does not exist, insert it with last_updated
                                else:
                                    #service_data = {'name': service_name, 'host': host, 'port': port, 'last_updated': datetime.now()}
                                    db.insert(table_name, (service_name,host,port,datetime.now()))
                                response = db.fetch_dict(table_name)
                            else:
                                raise cherrypy.HTTPError(400, "host and port are missing")
                        else:
                            raise cherrypy.HTTPError(400, "the service name provided is not part of the system")
                    else: 
                        raise cherrypy.HTTPError(400, "device_id or service_name is missing")
                    
                    return json.dumps(response, indent = 4)
                except HTTPError:
                    # Re-raise HTTPError if it's already a HTTPError
                    raise
                except Exception as e:
                    cherrypy.log(str(e))
                    raise HTTPError(500, f"Internal Server error {e}")
            
            #/table_name/...?parameter=value - modify element
            elif len(uri) > 0 and len(params) > 0: # Update table based on URI and params
                table_name = uri[0]
                response = {}
                # Extract conditions from URI
                conditions = self.get_condition_keys(table_name, uri)

                # Extract the first parameter from params (only 1 param)
                if len(params) != 1:
                    raise HTTPError(400, "Exactly one parameter is required")

                new_data_name, new_data_value = next(iter(params.items()))
                # Validate values
                #   ventilation, light and water_pump should be ON or OFF
                #   status_light should be GREEN, YELLOW or RED
                actuator_id = None
                if table_name == 'rooms':
                    if new_data_name == 'ventilation':
                        if new_data_value not in ['ON', 'OFF']:
                            raise HTTPError(400, "Invalid value for ventilation. Allowed values are 'ON' or 'OFF'")
                        actuator_id = 'ventilation_id'
                elif table_name == 'shelves':
                    if new_data_name in ['light', 'water_pump']:
                        if new_data_value not in ['ON', 'OFF']:
                            raise HTTPError(400, f"Invalid value for {new_data_name}. Allowed values are 'ON' or 'OFF'")
                        actuator_id = f'{new_data_name}_id'
                    elif new_data_name == 'status_light':
                        if new_data_value not in ['GREEN', 'YELLOW', 'RED']:
                            raise HTTPError(400, "Invalid value for status_light. Allowed values are 'GREEN', 'YELLOW', or 'RED'")
                        actuator_id = 'status_light_id'

                if actuator_id:
                    # Fetch the corresponding actuator_id based on conditions
                    actuator_data = db.fetch_dict(table_name, conditions)
                    if not actuator_data:
                        raise HTTPError(404, "Resource not found")

                    # Extract the actuator_id value
                    actuator_id_value = actuator_data[0][actuator_id]

                    # Update the database
                    db.update(table_name, {'condition': conditions, 'new_data': {new_data_name: new_data_value}})

                    # Prepare success response with actuator_id
                    response = {'actuator_id': actuator_id_value, 'status': new_data_value}
                    return json.dumps(response, indent=4)
                
                db.update(table_name, {'condition': conditions, 'new_data': {new_data_name: new_data_value}})
                response = db.fetch_dict(table_name,condition = conditions)
                return json.dumps(response, indent=4)

            else:
                raise HTTPError(404, "Page not found")
        except Exception as e:
            cherrypy.log(str(e))
            raise HTTPError(500, f"Internal Server error {e}")
        finally:
            db.close()

    def PUT(self, *uri, **params): # only for NEW resources
        db = DB(self.db_name)
        try:
            if len(uri) == 1:
                table_name = uri[0]
                # Check if the table exists in the database schema
                if table_name in db.tables():
                    # Extract data from JSON body of the request
                    try:
                        data = cherrypy.request.body.read().decode('utf-8')
                        data = json.loads(data)
                    except Exception as e:
                        raise HTTPError(400, "Invalid JSON data")

                    # Validate that all required fields are present in the JSON data
                    file_path = "table_schema.json"
                    # retrive only the table and columns names from the file
                    table_schema = {table_name: [column.split()[0] for column in columns] for table_name, columns in json.load(open(file_path)).items()}

                    if table_name not in table_schema:
                        raise HTTPError(400, "Invalid table name")

                    # Validate that all required fields are present in the JSON data
                    for field in table_schema[table_name]:
                        if field not in data:
                            raise HTTPError(400, f"Field '{field}' is missing in the JSON data")

                    # see if there are already data present with same keys
                    conditions = {}
                    key_fields = self.get_condition_keys(table_name,uri,only_names=True)
                    for key_field in key_fields:
                        if key_field in data:
                            conditions[key_field] = data[key_field]
                    
                    # check if there isn't already a data with the same ids
                    response = db.fetch(table_name, conditions)
                    if response:
                        raise HTTPError(409, f"Conflict with an element already in the table {table_name}")
                    else:
                        # Insert the data into the specified table
                        print(f"insert: {tuple(data[field] for field in table_schema[table_name])} in {table_name}")
                        db.insert(table_name, tuple(data[field] for field in table_schema[table_name]))
                    # return updated table
                    response = db.fetch_dict(table_name)
                    return json.dumps(response, indent=4)
                else:
                    raise HTTPError(404, "Table not found")
            else:
                raise HTTPError(404, "Page not found")
        except HTTPError as e:
            raise
        except Exception as e:
            cherrypy.log(str(e))
            raise HTTPError(500, f"Internal Server error: {e}")
        finally:
            db.close()
        

    def DELETE(self, *uri, **params):
        db = DB(self.db_name)
        try:
            if uri and uri[0] == "reset":
                self.prefill_database("reset_database.json")
                print("The database has been emptied.")
                export = db.export_json_all()
                return export
            
            # DELETE single row of table
            elif uri and len(uri) > 0 and len(params) == 0:
                table_name = uri[0]
                # Get conditions
                conditions = self.get_condition_keys(table_name, uri, delete = True)

                # Perform deletion based on conditions
                db.delete(table_name, conditions)
                print(f"The elements from {table_name} with conditions {conditions} have been deleted.")
                export = db.export_json_all()
                return export
            # DELETE table_name?param=value
            elif uri and len(uri) == 1 and len(params) > 0: # parameters present
                table_name = uri[0]
                conditions = {}
                for key, value in params.items():
                    conditions[key] = value
                
                db.delete(table_name,conditions)
                print(f"The elements from {table_name} with conditions {conditions} have been deleted.")

                # delete related elements

                condition_names = self.get_condition_keys(table_name,uri,only_names = True)
                
                constructed_uri = list(uri)
                # Append corresponding values from the conditions
                for key in condition_names:
                    if key in conditions:
                        constructed_uri.append(conditions[key])
                    else:
                        constructed_uri.append(None)  # Add None if no matching value

                c = self.get_condition_keys(table_name,constructed_uri,delete=True) # this eliminates the related rows in other tables
                print("The related tables have been updated.")
                
                export = db.export_json_all()
                return export
            else:
                raise HTTPError(404, "Page not found")
        except Exception as e:
            cherrypy.log(str(e))
            raise HTTPError(500, f"Internal Server error {e}")
        finally:
            db.close()

    def get_condition_keys(self, table_name, uri, delete = False, only_names = False):
        db = DB(self.db_name)
        conditions = {}
        if table_name == 'rooms':
            condition_keys = ['room_id']
            if delete and len(uri) > 2: # device_id was provided
                device_id = uri[2]
                key = 'device_id'
                conditions[key] = uri[2]
                return conditions
            elif only_names == False:
                # fetch device_id of that room
                key = 'room_id'
                conditions[key] = uri[1]
                device_id = db.search_first_value(table_name, conditions, key)
            
            if delete and len(uri) > 1: # need to delete related things fromt other tables
                table_name2 = "shelves"
                key = 'room_id'
                conditions[key] = uri[1]
                db.delete(table_name2, conditions)
                print(f"The elements from {table_name2} with conditions {conditions} have been deleted.")
                # disconnect the device from the room
                table_name2 = "topics"
                key = 'device_id'
                topics = db.fetch_dict(table_name2)
                conditions2 = {}
                for topic in topics:
                    conditions2[key] = device_id
                    db.delete(table_name2, conditions2)
                    print(f"The sensor from {table_name2} with conditions {conditions2} have been deleted.")
        elif table_name == 'shelves':
            condition_keys = ['room_id', 'tower_id', 'shelf_id']
        elif table_name == 'plants':
            condition_keys = ['plant_id']
            if delete and len(uri) > 0: # need to delete related things fromt other tables
                table_name2 = "shelves"
                key = 'plant_id'
                plant_id = uri[1]
                db.update(table_name2, {'condition': {'plant_id': plant_id}, 'new_data': {'plant_id': "", 'status': "", 'light': "OFF", 'water_pump' : "OFF"}}) # empty
                print(f"The elements from {table_name2} with conditions {conditions} have been deleted.")
        elif table_name == 'plant_types':
            condition_keys = ['type_id']
            if delete and len(uri) > 1: # need to delete related things fromt other tables
                key = 'type_id'
                
                table_name2 = "plant_nutrients"
                conditions[key] = uri[1]
                db.delete(table_name2, conditions)
                print(f"The elements from {table_name2} with conditions {conditions} have been deleted.")


                shelf_data = db.fetch_dict("shelves")
                # Fetch all plant_ids related to the type_id
                plants_id = db.search_all_values("plants", conditions, column_name='plant_id')

                if shelf_data:
                    shelves = db.fetch_dict("shelves")
                    for shelf in shelves:
                        # Delete all plants that match the retrieved plant_id values
                        for plant_id in plants_id:                            
                            if shelf["plant_id"] == plant_id:
                                db.update("shelves", {'condition': {'plant_id': plant_id}, 'new_data': {'plant_id': "", 'status': "", 'light': "OFF", 'water_pump' : "OFF"}}) # empty
                                print(f"shleves row of plant {plant_id} cleaned")
                
                table_name2 = "plants"
                
                conditions[key] = uri[1]
                db.delete(table_name2, conditions)
                print(f"The elements from {table_name2} with conditions {conditions} have been deleted.")
                
                # Now, delete the plant_types themselves finally
                conditions[key] = uri[1]
                db.delete("plant_types", conditions)
                print(f"The elements from plant_types with conditions {conditions} have been deleted.")

        elif table_name == 'plant_nutrients':
            condition_keys = ['type_id', 'state']
        elif table_name == 'topics':
            condition_keys = ['sensor_id', 'device_id']
        else:
            raise HTTPError(404, "Invalid table name")
        
        if only_names:
            return condition_keys
        else:
            conditions = {} # reset conditions
            for i, key in enumerate(condition_keys):
                if i < len(uri) - 1:
                    conditions[key] = uri[i + 1]
            return conditions

    # read table_schema.json file and create the tables
    def create_tables(self): 
        db = DB(self.db_name)
        file_path = "table_schema.json"
        with open(file_path, 'r') as file:
            tables = json.load(file)
        for table_name, columns in tables.items():
            db.new(table_name, columns)
        db.close()

    def prefill_database(self, prefill_file_path = "prefilled_database.json"):
        db = DB(self.db_name)
        db.reset_database(exept=['services']) # delete content of old database
        # Read pre-filled data from file
        with open(prefill_file_path, 'r') as file:
            prefill_data = json.load(file)
        for table_name, data in prefill_data.items():
            db.insert_list(table_name, data)
        db.close()

    def check_microservices(self):
        print("Checking which microservices are still up...")
        # Connect to the database
        db = DB(self.db_name)

        # Fetch all microservices from the 'services' table
        services = db.fetch_dict("services")

        # Check if there are any services in the table
        if not services:
            print("No microservices found in the service table.")
        else:
            # Loop through each microservice
            for service in services:
                host = service.get("host")
                port = service.get("port")
                service_name = service.get("name")  
                # Check if the microservice is reachable
                if self.check_microservice(host, port):
                    print(f"Microservice {service['name']} is up and running.")
                else:
                    print(f"Microservice {service['name']} is down.")
                    # delete the microservice from the service table
                    deletion_success = db.delete("services", condition={"name": service_name})
                    if deletion_success:
                        print(f"Microservice {service_name} has been deleted from the service registry.")
                    else:
                        print(f"Failed to delete microservice {service_name} from the database.")

        # Close the database connection
        db.close()

    # check if a microservice is reachable
    def check_microservice(self, host, port):
        url = f"http://{host}:{port}"
        print(f"Cheching {url} ...")
        try:
            responce = requests.get(url) # GET request
            if responce.ok:
                # Server is up
                return True
            else:
                # Server is down or unreachable
                return False
        except requests.ConnectionError:
            # Server is down or unreachable
            return False
    
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
