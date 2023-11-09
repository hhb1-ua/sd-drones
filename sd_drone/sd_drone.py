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

# def get_partition_number(topic):
#     consumer = kafka.KafkaConsumer(
#         bootstrap_servers = [BROKER_ADRESS])
#     return len(consumer.partitions_for_topic(topic))

class Drone:
    def __init__(self, identifier, alias):
        self.identifier = identifier    # Identificador interno
        self.alias      = alias         # Nombre interno
        self.token      = None          # Código de autentificación
        self.partition  = None          # Partición asignada

        self.x = 0
        self.y = 0

    def __str__(self):
        return json.dumps({
            "identifier": self.identifier,
            "alias": self.alias,
            "token": self.token,
            "partition": self.partition,
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

    def step_toward(self, target):
        if target["x"] < 0 or target["y"] < 0 or target["x"] >= SETTINGS["map"]["cols"] or target["y"] >= SETTINGS["map"]["rows"]:
            return False

        self.x += get_direction(self.x, target["x"])
        self.y += get_direction(self.y, target["y"])
        return True

    # def get_engine_key(self):
    #     try:
    #         server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         server.connect(ENGINE_ADRESS)
    #         server.send(json.dumps({"token": self.token}).encode("utf-8"))
    #
    #         response = server.recv(1024).decode("utf-8")
    #         response = json.loads(response)
    #
    #         server.close()
    #
    #         if response["accepted"]:
    #             self.partition = response["partition"]
    #             return True
    #
    #     except Exception as e:
    #         server.close()
    #         raise e
    #
    #     return False
    #
    # def get_drone_list(self):
    #     consumer = kafka.KafkaConsumer(
    #         "drone_list",
    #         bootstrap_servers = [f"{BROKER_ADRESS[0]}:{BROKER_ADRESS[1]}"],
    #         value_deserializer = lambda msg: msg.decode("utf-8"),
    #         consumer_timeout_ms = CONNECTION_TIMEOUT * 1000
    #     )
    #
    #     for message in consumer:
    #         self.print_map(json.loads(message.value)["drone_list"])
    #
    # def get_target(self):
    #     consumer = kafka.KafkaConsumer(
    #         bootstrap_servers = [f"{BROKER_ADRESS[0]}:{BROKER_ADRESS[1]}"],
    #         value_deserializer = lambda msg: msg.decode("utf-8"),
    #         consumer_timeout_ms = CONNECTION_TIMEOUT * 1000)
    #
    #     consumer.assign([kafka.TopicPartition("drone_target", self.partition)])
    #
    #     for message in consumer:
    #         if self.step_toward(json.loads(message.value)):
    #             self.publish_data()
    #
    # def publish_data(self):
    #     producer = kafka.KafkaProducer(
    #         bootstrap_servers = [BROKER_ADRESS],
    #         value_serializer = lambda message: message.encode("utf-8"))
    #     producer.send("drone_position", value = str(self), partition = self.partition)
    #
    # def print_map(self, drone_list):
    #     os.system("clear")
    #
    #     print(f"{self.alias} is currently at ({self.x}, {self.y})", end = "\n\n")
    #     for i in range(20):
    #         for j in range(20):
    #             if {"x": j, "y": i} in drone_list:
    #                 print("*", end = " ")
    #             else:
    #                 print(".", end = " ")
    #       print()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <identifier> <alias>")
        quit()

    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down.")
        quit()

    try:
        DRONE = Drone(int(sys.argv[1]), str(sys.argv[2]))
        print(f"Successfully created drone <{DRONE.alias}> with identifier <{DRONE.identifier}>")
    except Exception as e:
        print(str(e))
        print("Service stopped abruptly, shutting down.")
        quit()

    if DRONE.identity_register():
        print(f"Received token <{DRONE.token}>")
    else:
        print("Couldn't connect to registry server, shutting down.")
        quit()

    # threading.Thread(target = drone.get_drone_list, args = None).start()
    # threading.Thread(target = drone.get_target, args = None).start()

    # try:
    #     if input("Connect to engine? (y/N) ") is "y":
    #         drone.main_loop(BROKER_ADRESS[0], BROKER_ADRESS[1])
    #     else:
    #         quit()
    # except Exception as e:
    #     print(str(e))
    #     quit()



