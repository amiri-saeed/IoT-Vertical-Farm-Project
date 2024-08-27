'''
This would allow us to handle receving payloads in external broker
This woould also allow us to establish communication with TS's broker and write at the ThingSpeak Platform

tested pub_to_exb_test.py and working
'''


import json
import time
import paho.mqtt.client as PahoMQTT


class MyMQTT:
    def __init__(self, clientID, username, password, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self.clientID = clientID
        self._topic = ""
        self._isSubscriber = False

        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(clientID, True)
        
        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

        if username != "" and password != "":
            self._paho_mqtt.username_pw_set(username, password)

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.broker, rc))

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, topic, msg):
        # publish a message with a certain topic
        self._paho_mqtt.publish(topic, json.dumps(msg), 2)

    def mySubscribe(self, topic):

        # subscribe for a topic
        self._paho_mqtt.subscribe(topic, 2)
        # just to remember that it works also as a subscriber
        self._isSubscriber = True
        self._topic = topic
        print("subscribed to %s" % (topic))

    def start(self):
        # manage connection to broker
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def unsubscribe(self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber
            self._paho_mqtt.unsubscribe(self._topic)

    def stop(self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber
            self._paho_mqtt.unsubscribe(self._topic)

        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()





class TSPublisher:
    def __init__(self, clientID, username, password, broker, port):
        self.client = MyMQTT(clientID, username, password, broker, port, None)

    def startSim(self):
        self.client.start()

    def stopSim(self):
        self.client.stop()

    def publish(self, topic, value):
        self.client.myPublish(topic, value)




class ExternalSubscriber:
    def __init__(self, clientID, broker, port, topic, manager_instance):
        self.client = MyMQTT(clientID, "", "", broker, port, self)
        self.topic = topic
        self.manager_instance = manager_instance

    # def notify(self, topic, payload):
    #     self.manager_instance.add_external_payload(topic, json.loads(payload))

    def notify(self, topic, payload):
        try:
            print("Received payload:", payload)
            print("Type of payload:", type(payload))
            
            # Check if payload is already a dictionary
            if isinstance(payload, dict):
                self.manager_instance.add_external_payload(topic, payload)
            else:
                # Attempt to parse payload as JSON string
                parsed_payload = json.loads(payload)
                self.manager_instance.add_external_payload(topic, parsed_payload)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON payload: {e}")
        except Exception as e:
            logging.error(f"Error in notify method: {e}")

    def startSim(self):
        self.client.start()
        self.client.mySubscribe(self.topic)

    def stopSim(self):
        self.client.unsubscribe()
        self.client.stop()


