# TODO: Imprimir bien el mapa
# TODO: Modificar los datos del dron
# TODO: Borrar el dron de la base de datos
# TODO: Código de autentificación para operaciones

import json
import socket
import sys
import os
import threading
import time
import kafka

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
    def __init__(self, identifier, alias, token = None):
        self.identifier = identifier    # Identificador interno
        self.alias      = alias         # Nombre interno
        self.token      = token         # Código de autentificación

        self.x = 0
        self.y = 0

        if token is None:
            if not call_repeatedly(self.identity_register):
                raise Exception("Couldn't connect to registry server")

        if not call_repeatedly(self.identity_authenticate):
            raise Exception("Couldn't authenticate in engine server")

        try:
            threading.Thread(target = self.track_drone_list, args = ()).start()
            threading.Thread(target = self.track_drone_target, args = ()).start()
        except Exception as e:
            raise e

    def __str__(self):
        return json.dumps({
            "identifier": self.identifier,
            "alias": self.alias,
            "token": self.token,
            "position": {
                "x": self.x,
                "y": self.y
            }
        })

    def identity_register(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((SETTINGS["adress"]["registry"]["host"], SETTINGS["adress"]["registry"]["port"]))
            message = json.dumps({
                "operation": "register",
                "identifier": self.identifier,
                "alias": self.alias
            })
            server.send(message.encode(SETTINGS["message"]["codification"]))
            response = json.loads(server.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"]))
            server.close()

            if response["accepted"]:
                self.token = response["token"]
                return True
            return False

        except Exception as e:
            return False

    def identity_modify(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((SETTINGS["adress"]["registry"]["host"], SETTINGS["adress"]["registry"]["port"]))
            message = json.dumps({
                "operation": "modify",
                "identifier": self.identifier,
                "alias": self.alias
            })
            server.send(message.encode(SETTINGS["message"]["codification"]))
            response = json.loads(server.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"]))
            server.close()

            return response["accepted"]

        except Exception as e:
            return False

    def identity_delete(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((SETTINGS["adress"]["registry"]["host"], SETTINGS["adress"]["registry"]["port"]))
            message = json.dumps({
                "operation": "delete",
                "identifier": self.identifier
            })
            server.send(message.encode(SETTINGS["message"]["codification"]))
            response = json.loads(server.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"]))
            server.close()

            return response["accepted"]

        except Exception as e:
            return False

    def identity_authenticate(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((SETTINGS["adress"]["authentication"]["host"], SETTINGS["adress"]["authentication"]["port"]))
            server.send(json.dumps({"token": self.token}).encode(SETTINGS["message"]["codification"]))
            response = json.loads(server.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"]))
            server.close()

            return response["accepted"]

        except Exception as e:
            raise e

    def step_toward(self, target):
        if target["x"] < 0 or target["y"] < 0 or target["x"] >= SETTINGS["map"]["cols"] or target["y"] >= SETTINGS["map"]["rows"]:
            return False

        self.x += get_direction(self.x, target["x"])
        self.y += get_direction(self.y, target["y"])
        return True

    def track_drone_list(self):
        consumer = kafka.KafkaConsumer(
            "drone_list",
            bootstrap_servers = [str(SETTINGS["adress"]["broker"]["host"]) + ":" + str(SETTINGS["adress"]["broker"]["port"])],
            value_deserializer = lambda msg: msg.decode(SETTINGS["message"]["codification"]),
            consumer_timeout_ms = SETTINGS["message"]["timeout"] * 1000)

        for message in consumer:
            self.print_map(json.loads(message.value)["drone_list"])

    def track_drone_target(self):
        consumer = kafka.KafkaConsumer(
            bootstrap_servers = [str(SETTINGS["adress"]["broker"]["host"]) + ":" + str(SETTINGS["adress"]["broker"]["port"])],
            value_deserializer = lambda msg: msg.decode(SETTINGS["message"]["codification"]))
        consumer.assign([kafka.TopicPartition("drone_target", self.identifier)])

        producer = kafka.KafkaProducer(
            bootstrap_servers = [str(SETTINGS["adress"]["broker"]["host"]) + ":" + str(SETTINGS["adress"]["broker"]["port"])],
            value_serializer = lambda msg: msg.encode(SETTINGS["message"]["codification"]))

        for message in consumer:
            if not self.step_toward(json.loads(message.value)):
                print("Couldn't step towards target, out of bounds.")
            producer.send("drone_position", value = str(self), partition = self.identifier)

    def print_map(self, drone_list):
        print(f"Drone <{self.alias}> is currently at ({self.x}, {self.y})")

        # TODO
        # for i in range(SETTINGS["map"]["rows"]):
        #     for j in range(SETTINGS["map"]["cols"]):
        #         if {"x": j, "y": i} in drone_list:
        #             print("*", end = " ")
        #         else:
        #             print(".", end = " ")

if __name__ == "__main__":
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <identifier> <alias> [token]")
        quit()

    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down")
        quit()

    try:
        if len(sys.argv) == 3:
            DRONE = Drone(int(sys.argv[1]), str(sys.argv[2]))
        else:
            if str(sys.argv[3]) == "null":
                DRONE = Drone(int(sys.argv[1]), str(sys.argv[2]))
            else:
                DRONE = Drone(int(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
        print(f"Successfully created drone <{DRONE.alias}> with identifier <{DRONE.identifier}>")
    except Exception as e:
        print(str(e))
        print("Service stopped abruptly, shutting down")
        quit()



