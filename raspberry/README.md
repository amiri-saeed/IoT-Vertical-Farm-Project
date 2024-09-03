# smart_IoT-Vertical-Farm
Programming for IoT Polito 2023/2024


# API
Here there are the API that must be used to interact with the actuators in our farm.

POST http://192.168.1.254:8080/
Body:
    {
        "actuator": :actuator,
        "command" : :command
    }

More details in API.http file.
