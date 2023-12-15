import json
import sys
import os
import threading
import time
import kafka
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

SETTINGS    = None
DRONE       = None

def get_direction(a, b):
    d = b - a

    if d > 0:
        return 1
    if d < 0:
        return -1
    return 0

def call_repeatedly(function):
    timer = 2
    while timer <= SETTINGS["message"]["timeout"]:
        if function():
            return True
        time.sleep(timer)
        timer *= 2
    return False

class Drone:
    def __init__(self, identifier, alias, password):
        self.identifier = identifier    # Identificador
        self.alias      = alias         # Nombre
        self.password   = password      # Contraseña

        self.x = 0
        self.y = 0

        # try:
        #     threading.Thread(target = self.track_drone_list, args = ()).start()
        #     threading.Thread(target = self.track_drone_target, args = ()).start()
        # except Exception as e:
        #     raise e

    def __str__(self):
        return json.dumps({
            "identifier": self.identifier,
            "alias": self.alias,
            "password": self.password,
            "token": self.token,
            "position": {
                "x": self.x,
                "y": self.y
            }
        })

    def register_drone(self):
        api = f"https://{SETTINGS['address']['registry']['host']}:{SETTINGS['address']['registry']['port']}/register_drone"
        try:
            return requests.post(api, json = {"identifier": self.identifier, "alias": self.alias, "password": self.password}, verify = False).status_code == 200
        except Exception as e:
            return False

    def request_token(self):
        api = f"https://{SETTINGS['address']['registry']['host']}:{SETTINGS['address']['registry']['port']}/request_token"
        try:
            response = requests.post(api, json = {"identifier": self.identifier, "password": self.password}, verify = False)
            if response.status_code == 200:
                return response.json()["token"]
            return None
        except Exception as e:
            return None

    def authenticate_drone(self):
        # TODO
        return False

    def step_toward(self, target):
        if target["x"] < 0 or target["y"] < 0 or target["x"] >= SETTINGS["map"]["cols"] or target["y"] >= SETTINGS["map"]["rows"]:
            return False

        self.x += get_direction(self.x, target["x"])
        self.y += get_direction(self.y, target["y"])
        return True

    def track_drone_list(self):
        consumer = kafka.KafkaConsumer(
            bootstrap_servers = [str(SETTINGS["adress"]["broker"]["host"]) + ":" + str(SETTINGS["adress"]["broker"]["port"])],
            value_deserializer = lambda msg: json.loads(msg.decode(SETTINGS["message"]["codification"])),
            consumer_timeout_ms = SETTINGS["message"]["timeout"] * 1000)
        consumer.assign([kafka.TopicPartition("drone_list", 0)])

        for message in consumer:
            print("\033c", end = "")
            print(f"Drone <{self.identifier}> with alias <{self.alias}> is currently at ({self.x}, {self.y})")
            print(message.value["map"])

    def track_drone_target(self):
        consumer = kafka.KafkaConsumer(
            bootstrap_servers = [str(SETTINGS["adress"]["broker"]["host"]) + ":" + str(SETTINGS["adress"]["broker"]["port"])],
            value_deserializer = lambda msg: json.loads(msg.decode(SETTINGS["message"]["codification"])))
        consumer.assign([kafka.TopicPartition("drone_target", self.identifier)])

        producer = kafka.KafkaProducer(
            bootstrap_servers = [str(SETTINGS["adress"]["broker"]["host"]) + ":" + str(SETTINGS["adress"]["broker"]["port"])],
            value_serializer = lambda msg: msg.encode(SETTINGS["message"]["codification"]))

        for message in consumer:
            if not self.step_toward(message.value):
                print("Couldn't step towards target, out of bounds")
            producer.send("drone_position", value = str(self), partition = self.identifier)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <identifier> <alias> <password>")
        quit()

    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Couldn't load settings file 'settings.json', shutting down")
        quit()

    # WARNING: Desactivadas alertas de SSL autofirmado
    warnings.simplefilter("ignore", InsecureRequestWarning)

    try:
        DRONE = Drone(int(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))

        if not DRONE.register_drone():
            print("Couldn't register drone, shutting down")
            quit()

        token = DRONE.request_token()
        if token is None:
            print("Couldn't get authentication token, shutting down")
            quit()

        if not DRONE.authenticate_drone(token):
            print("Couldn't authenticate in Engine, shutting down")
            quit()

    except Exception as e:
        raise e
        print(str(e))
        print("Service stopped abruptly, shutting down")
        quit()



