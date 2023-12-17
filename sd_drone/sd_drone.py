import json
import sys
import os
import threading
import time
import kafka
import requests
import warnings
from cryptography.fernet import Fernet
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
        self.crypto     = None          # Clave de cifrado

        self.x = 0
        self.y = 0

    def start_services(self):
        try:
            threading.Thread(target = self.track_drone_list, args = ()).start()
            threading.Thread(target = self.track_drone_target, args = ()).start()
        except Exception as e:
            raise e

    def __str__(self):
        return json.dumps({
            "identifier": self.identifier,
            "alias": self.alias,
            "password": self.password,
            "crypto": self.crypto.decode(SETTINGS["message"]["codification"]),
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

    def authenticate_drone(self, token):
        api = f"https://{SETTINGS['address']['authenticate']['host']}:{SETTINGS['address']['authenticate']['port']}/authenticate_drone"
        try:
            response = requests.post(api, json = {"identifier": self.identifier, "password": self.password, "token": token}, verify = False)
            if response.status_code == 200:
                data = response.json()
                self.crypto = bytes(data["crypto"], "utf-8")
                self.x = data["position"]["x"]
                self.y = data["position"]["y"]
                return True
            return False
        except Exception as e:
            raise e
            return False

    def step_toward(self, target):
        if target["x"] < 0 or target["y"] < 0 or target["x"] >= SETTINGS["map"]["cols"] or target["y"] >= SETTINGS["map"]["rows"]:
            return False

        self.x += get_direction(self.x, target["x"])
        self.y += get_direction(self.y, target["y"])
        return True

    def track_drone_list(self):
        fernet = Fernet(self.crypto)

        consumer = kafka.KafkaConsumer(
            bootstrap_servers = [str(SETTINGS["address"]["broker"]["host"]) + ":" + str(SETTINGS["address"]["broker"]["port"])])
        consumer.assign([kafka.TopicPartition("drone_list", self.identifier)])

        for message in consumer:
            try:
                data = json.loads(fernet.decrypt(message).decode(SETTINGS["message"]["codification"]))

                if not SETTINGS["debug"]:
                    print("\033c", end = "")
                print(f"Drone <{self.identifier}> with alias <{self.alias}> is currently at ({self.x}, {self.y})")
                print(data["map"])
            except Exception as e:
                # Error al desencriptar el mensaje
                raise e
                print(f"Couldn't decrypt message, incorrect token ({str(e)})")
                break

    def track_drone_target(self):
        fernet = Fernet(self.crypto)

        consumer = kafka.KafkaConsumer(
            bootstrap_servers = [str(SETTINGS["address"]["broker"]["host"]) + ":" + str(SETTINGS["address"]["broker"]["port"])])
        consumer.assign([kafka.TopicPartition("drone_target", self.identifier)])

        producer = kafka.KafkaProducer(
            bootstrap_servers = [str(SETTINGS["address"]["broker"]["host"]) + ":" + str(SETTINGS["address"]["broker"]["port"])],
            value_serializer = lambda msg: fernet.encrypt(msg.encode("utf-8")))

        for message in consumer:
            try:
                data = json.loads(fernet.decrypt(message.value))

                if not self.step_toward(data):
                    print("Couldn't step towards target, out of bounds")
                producer.send("drone_position", value = str(self), partition = self.identifier)
            except Exception as e:
                # Error al desencriptar el mensaje
                raise e
                print(f"Couldn't decrypt message, incorrect token ({str(e)})")
                break

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

        print(str(DRONE))
        DRONE.start_services()

    except Exception as e:
        print(str(DRONE.crypto))
        print(str(e))
        print("Service stopped abruptly, shutting down")
        quit()



