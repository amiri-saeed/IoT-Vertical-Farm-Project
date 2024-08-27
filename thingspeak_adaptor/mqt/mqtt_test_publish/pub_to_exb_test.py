from MyMQTT import *
import random
import time
import threading
import datetime

# class Publisher:
#     def __init__(self, clientID, broker, port):
#         self.client = MyMQTT(clientID, broker, port, None)
#         self.client.start()

#     def publish(self, topic, payload):
#         self.client.myPublish(topic, payload)

#     def stop(self):
#         self.client.stop()

# def generate_payload(additional_sensor):
#     common_sensors = [
#         {"n": "height", "u": "m", "v": random.uniform(5, 25)},
#         {"n": "li", "u": "lux", "v": random.uniform(50, 200)},
#         {"n": "pH", "u": "pH", "v": random.uniform(5.5, 7.5)},
#         {"n": "n", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "k", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "p", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "moisture", "u": "%", "v": random.uniform(60, 100)}
#     ]
#     additional_sensors = {
#         "temp": {"n": "temp", "u": "°C", "v": random.uniform(20, 30)},
#         "co2": {"n": "co2", "u": "ppm", "v": random.uniform(100, 1500)},
#         "humid": {"n": "humid", "u": "%", "v": random.uniform(50, 60)},
#         "water": {"n": "water", "u": "L", "v": random.uniform(40, 60)}
#     }
#     payload = {
#         "e": common_sensors + [additional_sensors[additional_sensor]],
#         "bn": ""
#     }
#     return payload

# def publish_payloads():
#     broker = "mqtt.eclipseprojects.io"
#     port = 1883
#     publisher = Publisher("diego", broker, port)

#     topics = [
#         "pub/R1/T1/S1/temp",
#         "pub/R1/T1/S2/humid",
#         "pub/R1/T2/S1/co2",
#         "pub/R1/T2/S2/water"
#     ]
#     additional_sensors = ["temp", "humid", "co2", "water"]


#     try:
#         for i in range(4):
#             payload = generate_payload(additional_sensors[i])
#             publisher.publish(topics[i], payload)
#             print(f"Payload published to topic: {topics[i]}")
#             time.sleep(30)
#     finally:
#         publisher.stop()

# if __name__ == "__main__":
#     while True:
#         publish_payloads()

# class Publisher:
#     def __init__(self, clientID, broker, port):
#         self.client = MyMQTT(clientID, broker, port, None)
#         self.client.start()

#     def publish(self, topic, payload):
#         self.client.myPublish(topic, payload)

#     def stop(self):
#         self.client.stop()

# def generate_payload(initial_height, growth_rate, additional_sensor):
#     current_height = initial_height + growth_rate
#     common_sensors = [
#         {"n": "height", "u": "m", "v": current_height},
#         {"n": "li", "u": "lux", "v": random.uniform(50, 200)},
#         {"n": "pH", "u": "pH", "v": random.uniform(5.5, 7.5)},
#         {"n": "n", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "k", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "p", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "moisture", "u": "%", "v": random.uniform(60, 100)}
#     ]
#     additional_sensors = {
#         "temp": {"n": "temp", "u": "°C", "v": random.uniform(20, 30)},
#         "co2": {"n": "co2", "u": "ppm", "v": random.uniform(100, 1500)},
#         "humid": {"n": "humid", "u": "%", "v": random.uniform(50, 60)},
#         "water": {"n": "water", "u": "L", "v": random.uniform(40, 60)}
#     }
#     payload = {
#         "e": common_sensors + [additional_sensors[additional_sensor]],
#         "bn": "PlantSensorData"
#     }
#     return payload, current_height

# def publish_payloads(total_duration, interval):
#     broker = "mqtt.eclipseprojects.io"
#     port = 1883
#     publisher = Publisher("diego", broker, port)

#     topics = [
#         "pub/R1/T1/S1/temp",
#         "pub/R1/T1/S2/humid",
#         "pub/R1/T2/S1/co2",
#         "pub/R1/T2/S2/water"
#     ]
#     additional_sensors = ["temp", "humid", "co2", "water"]

#     initial_height = random.uniform(4, 8)  # Initial height of the plant in meters
#     growth_rate_per_interval = random.uniform(0.2, 0.5)  # Growth rate in meters per interval

#     total_intervals = int(total_duration / interval)

#     try:
#         current_height = initial_height
#         for i in range(total_intervals):
#             print(f"Time: {datetime.datetime.now()} | Interval: {i+1}/{total_intervals}")
#             for j in range(len(topics)):
#                 payload, current_height = generate_payload(current_height, growth_rate_per_interval, additional_sensors[j])
#                 publisher.publish(topics[j], payload)
#                 print(f"Payload published to topic: {topics[j]}")
#                 print(f"Current Plant Height: {current_height:.2f} m")
#             time.sleep(interval)
#     finally:
#         publisher.stop()

# if __name__ == "__main__":
#     # Example usage:
#     total_duration = 20 # 10 minutes
#     interval = 60  # Every 30 seconds
#     publish_payloads(total_duration*60, interval)



# import time
# import random
# import datetime

# class Publisher:
#     def __init__(self, clientID, broker, port):
#         self.client = MyMQTT(clientID, broker, port, None)
#         self.client.start()

#     def publish(self, topic, payload):
#         self.client.myPublish(topic, payload)

#     def stop(self):
#         self.client.stop()

# def generate_payload(initial_height, growth_rate, sensor_values, sensor_increments, additional_sensor):
#     current_height = initial_height + growth_rate
    
#     # Update the sensor values based on their respective increments
#     sensor_values["temp"] += sensor_increments["temp"]
#     sensor_values["co2"] += sensor_increments["co2"]
#     sensor_values["humid"] += sensor_increments["humid"]

#     common_sensors = [
#         {"n": "height", "u": "m", "v": current_height},
#         {"n": "li", "u": "lux", "v": random.uniform(50, 200)},
#         {"n": "pH", "u": "pH", "v": random.uniform(5.5, 7.5)},
#         {"n": "n", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "k", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "p", "u": "mg/L", "v": random.uniform(1, 4)},
#         {"n": "moisture", "u": "%", "v": random.uniform(60, 100)}
#     ]
#     additional_sensors = {
#         "temp": {"n": "temp", "u": "°C", "v": sensor_values["temp"]},
#         "co2": {"n": "co2", "u": "ppm", "v": sensor_values["co2"]},
#         "humid": {"n": "humid", "u": "%", "v": sensor_values["humid"]},
#         "water": {"n": "water", "u": "L", "v": random.uniform(40, 60)}
#     }
#     payload = {
#         "e": common_sensors + [additional_sensors[additional_sensor]],
#         "bn": "PlantSensorData"
#     }
#     return payload, current_height, sensor_values

# def publish_payloads(total_duration, interval):
#     broker = "mqtt.eclipseprojects.io"
#     port = 1883
#     publisher = Publisher("diego", broker, port)

#     topics = [
#         "pub/R1/T1/S1/temp",
#         "pub/R1/T1/S2/humid",
#         "pub/R1/T2/S1/co2",
#         "pub/R1/T2/S2/water"
#     ]
#     additional_sensors = ["temp", "humid", "co2", "water"]

#     initial_height = random.uniform(4, 8)  # Initial height of the plant in meters
#     growth_rate_per_interval = random.uniform(0.3, 0.7)  # Growth rate in meters per interval

#     # Initial sensor values and increments for simulation
#     sensor_values = {
#         "temp": random.uniform(14, 18),
#         "co2": random.uniform(350, 400),
#         "humid": random.uniform(45, 48)
#     }
#     sensor_increments = {
#         "temp": random.uniform(0.4, 0.7),  # Temperature increase per interval
#         "co2": random.uniform(25, 60),     # CO2 increase per interval
#         "humid": random.uniform(0.1, 0.5)  # Humidity increase per interval
#     }

#     total_intervals = int(total_duration / interval)

#     try:
#         current_height = initial_height
#         for i in range(total_intervals):
#             print(f"Time: {datetime.datetime.now()} | Interval: {i+1}/{total_intervals}")
#             for j in range(len(topics)):
#                 payload, current_height, sensor_values = generate_payload(
#                     current_height, growth_rate_per_interval, sensor_values, sensor_increments, additional_sensors[j]
#                 )
#                 publisher.publish(topics[j], payload)
#                 print(f"Payload published to topic: {topics[j]}")
#                 print(f"Current Plant Height: {current_height:.2f} m")
#                 print(f"Current Sensor Values: {sensor_values}")
#             time.sleep(interval)
#     finally:
#         publisher.stop()

# if __name__ == "__main__":
#     # Example usage:
#     total_duration = 20  # 20 minutes
#     interval = 60  # Every 60 seconds
#     publish_payloads(total_duration * 60, interval)


import time
import random
import datetime

class Publisher:
    def __init__(self, clientID, broker, port):
        self.client = MyMQTT(clientID, broker, port, None)
        self.client.start()

    def publish(self, topic, payload):
        self.client.myPublish(topic, payload)

    def stop(self):
        self.client.stop()

def generate_payload(initial_height, growth_rate, sensor_values, sensor_increments, additional_sensor):
    current_height = initial_height + growth_rate
    
    # Update the sensor values based on their respective increments
    sensor_values["temp"] += sensor_increments["temp"]
    sensor_values["co2"] += sensor_increments["co2"]
    sensor_values["humid"] += sensor_increments["humid"]
    sensor_values["moisture"] += sensor_increments["moisture"]
    sensor_values["water"] += sensor_increments["water"]

    common_sensors = [
        {"n": "height", "u": "m", "v": current_height},
        {"n": "li", "u": "lux", "v": random.uniform(50, 200)},
        {"n": "pH", "u": "pH", "v": random.uniform(5.5, 7.5)},
        {"n": "n", "u": "mg/L", "v": random.uniform(1, 4)},
        {"n": "k", "u": "mg/L", "v": random.uniform(1, 4)},
        {"n": "p", "u": "mg/L", "v": random.uniform(1, 4)},
        {"n": "moisture", "u": "%", "v": sensor_values["moisture"]}
    ]
    additional_sensors = {
        "temp": {"n": "temp", "u": "°C", "v": sensor_values["temp"]},
        "co2": {"n": "co2", "u": "ppm", "v": sensor_values["co2"]},
        "humid": {"n": "humid", "u": "%", "v": sensor_values["humid"]},
        "water": {"n": "water", "u": "L", "v": sensor_values["water"]}
    }
    payload = {
        "e": common_sensors + [additional_sensors[additional_sensor]],
        "bn": "PlantSensorData"
    }
    return payload, current_height, sensor_values

def publish_payloads(total_duration, interval):
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    publisher = Publisher("diego", broker, port)

    topics = [
        "pub/R1/T1/S1/temp",
        "pub/R1/T1/S2/humid",
        "pub/R1/T2/S1/co2",
        "pub/R1/T2/S2/water"
    ]
    additional_sensors = ["temp", "humid", "co2", "water"]

    initial_height = random.uniform(4, 8)  # Initial height of the plant in meters
    growth_rate_per_interval = random.uniform(0.2, 0.5)  # Growth rate in meters per interval

    # Initial sensor values and increments for simulation
    sensor_values = {
        "temp": random.uniform(20, 25),
        "co2": random.uniform(300, 400),
        "humid": random.uniform(50, 55),
        "moisture": random.uniform(40, 50),  # Initial moisture percentage
        "water": random.uniform(35, 40)     # Initial water level in liters
    }
    sensor_increments = {
        "temp": random.uniform(0.1, 0.3),   # Temperature increase per interval
        "co2": random.uniform(10, 50),      # CO2 increase per interval
        "humid": random.uniform(0.5, 1.5),  # Humidity increase per interval
        "moisture": random.uniform(1, 2),  # Moisture increase per interval
        "water": random.uniform(1, 1.5)   # Water level increase per interval
    }

    total_intervals = int(total_duration / interval)

    try:
        current_height = initial_height
        for i in range(total_intervals):
            print(f"Time: {datetime.datetime.now()} | Interval: {i+1}/{total_intervals}")
            for j in range(len(topics)):
                payload, current_height, sensor_values = generate_payload(
                    current_height, growth_rate_per_interval, sensor_values, sensor_increments, additional_sensors[j]
                )
                publisher.publish(topics[j], payload)
                print(f"Payload published to topic: {topics[j]}")
                print(f"Current Plant Height: {current_height:.2f} m")
                print(f"Current Sensor Values: {sensor_values}")
            time.sleep(interval)
    finally:
        publisher.stop()

if __name__ == "__main__":
    # Example usage:
    total_duration = 20  # 20 minutes
    interval = 60  # Every 60 seconds
    publish_payloads(total_duration * 60, interval)
