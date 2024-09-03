#include <ArduinoMqttClient.h>
#include <WiFiNINA.h>
#include "arduino_secrets.h"
#include <ArduinoJson.h>

// In arduino_secrets.h
char ssid[] = SECRET_SSID;    // network SSID (name)
char pass[] = SECRET_PASS;    // network password (use for WPA, or use as key for WEP)

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "mqtt.eclipseprojects.io";
int        port     = 1883;
const char topic[]  = "pub/R1/T1/S1/brightness_sensor";
// const char topic2[]  = "real_unique_topic_2";
// const char topic3[]  = "real_unique_topic_3";

//set interval for sending messages (milliseconds)
const long interval = 30000;
unsigned long previousMillis = 0;

int count = 0;

void setup() {
  //Initialize serial and wait for port to open:
  // Serial.begin(9600);
  // while (!Serial) {
  //   ; // wait for serial port to connect. Needed for native USB port only
  // }

  // attempt to connect to Wifi network:
  // Serial.print("Attempting to connect to WPA SSID: ");
  // Serial.println(ssid);
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    // failed, retry
    // Serial.print(".");
    delay(5000);
  }

  // Serial.println("You're connected to the network");
  // Serial.println();

  // Serial.print("Attempting to connect to the MQTT broker: ");
  // Serial.println(broker);

  if (!mqttClient.connect(broker, port)) {
    // Serial.print("MQTT connection failed! Error code = ");
    // Serial.println(mqttClient.connectError());
    while (1);
  }

  // Serial.println("You're connected to the MQTT broker!");
  // Serial.println();
}

void loop() {
  // call poll() regularly to allow the library to send MQTT keep alive which
  // avoids being disconnected by the broker
  mqttClient.poll();

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    // save the last time a message was sent
    previousMillis = currentMillis;

    // reads the input on analog pin A1 (value between 0 and 1023)
    int analogValue = analogRead(A1);

    Serial.print("Sending message to topic: ");
    // Serial.println(topic);
    // Serial.println(analogValue);

    // Formatting the message into a JSON:
    JsonDocument message;
    JsonObject root = message.to<JsonObject>(); // Create the main object
    //JsonArray elements = root.createNestedArray("e"); // Create the "e" array
    JsonArray elements = root["e"].to<JsonArray>(); // Create the "e" array
    JsonObject element = elements.add<JsonObject>(); // Create the first element in "e"
    element["n"] = "li"; // Add key-value pair "n": "li"
    element["u"] = "lum"; // Add key-value pair "u": "lum"
    element["v"] = analogValue;   // Add key-value pair "v": 6.8

    root["bn"] = "brightness_sensor"; // Add key-value pair "bn": "brightness_sensor"

//    serializeJson(message, Serial);
    // Serialize JSON to a character array
    char buffer[256];
    serializeJson(message, buffer, sizeof(buffer));

    // send message, the Print interface can be used to set the message contents
    mqttClient.beginMessage(topic);
    mqttClient.print(buffer);  // send the value get from the sensor
    mqttClient.endMessage();

    // Serial.println();
  }
}
