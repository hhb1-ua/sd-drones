import json
import socket
import sys
import os
import threading
import time
import kafka

ENGINE_ADRESS = ("engine", 9010)
REGISTRY_ADRESS =  ("registry", 9020)
BROKER_ADRESS =  ("kafka", 9092)
CONNECTION_TIMEOUT = 20

class Drone:
    def __init__(self, identifier, alias):
        self.identifier = identifier    # Identificador interno
        self.alias = alias              # Nombre interno
        self.token = None               # Código de autentificación
        self.partition = None           # Partición asignada
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

    # MÉTODOS DE AUTENTIFICACIÓN

    def identity_register(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((REGISTRY_ADRESS[0], REGISTRY_ADRESS[1]))

            message = json.dumps({
                "operation": "register",
                "identifier": self.identifier,
                "alias": self.alias
            })
            server.send(message.encode("utf-8"))

            response = server.recv(1024).decode("utf-8")
            response = json.loads(response)

            server.close()

            if response["accepted"]:
                self.token = response["token"]
                return True

        except Exception as e:
            server.close()
            raise e

        return False

    def identity_modify(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((REGISTRY_ADRESS[0], REGISTRY_ADRESS[1]))

            message = json.dumps({
                "operation": "modify",
                "identifier": self.identifier,
                "alias": self.alias
            })
            server.send(message.encode("utf-8"))

            response = server.recv(1024).decode("utf-8")
            response = json.loads(response)

            server.close()

            return response["accepted"]

        except Exception as e:
            server.close()
            raise e

        return False

    def identity_delete(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((REGISTRY_ADRESS[0], REGISTRY_ADRESS[1]))

            message = json.dumps({
                "operation": "delete",
                "identifier": self.identifier
            })
            server.send(message.encode("utf-8"))

            response = server.recv(1024).decode("utf-8")
            response = json.loads(response)

            server.close()

            return response["accepted"]

        except Exception as e:
            server.close()
            raise e

        return False

    # MÉTODOS DE MOVIMIENTO

    def step_toward(self, target):
        # Comprobar que la posición está dentro del mapa
        if target["x"] < 0 or target["y"] < 0 or target["x"] >= 20 or target["y"] >= 20:
            return False

        # Mover el dron
        self.x += get_direction(self.x, target["x"])
        self.y += get_direction(self.y, target["y"])

        return True

    # MÉTODOS DE COORDINACIÓN CON EL MOTOR

    def get_drone_list(self):
        consumer = kafka.KafkaConsumer(
            "drone_list",
            bootstrap_servers = [f"{BROKER_ADRESS[0]}:{BROKER_ADRESS[1]}"],
            value_deserializer = lambda msg: msg.decode("utf-8"),
            consumer_timeout_ms = CONNECTION_TIMEOUT * 1000
        )

        for message in consumer:
            self.print_map(json.loads(message.value)["drone_list"])

    def get_target(self):
        consumer = kafka.KafkaConsumer(
            bootstrap_servers = [f"{BROKER_ADRESS[0]}:{BROKER_ADRESS[1]}"],
            value_deserializer = lambda msg: msg.decode("utf-8"),
            consumer_timeout_ms = CONNECTION_TIMEOUT * 1000
        )

        consumer.assign([kafka.TopicPartition("drone_target", self.partition)])

        for message in consumer:
            if self.step_toward(json.loads(message.value)):
                self.publish_data()

    def publish_data(self):
        producer = kafka.KafkaProducer(
            bootstrap_servers = [BROKER_ADRESS],
            value_serializer = lambda message: message.encode("utf-8")
        )
        producer.send(topic, value = str(self))

    # MÉTODOS DE INTERFAZ DE USUARIO

    def print_map(self, drone_list):
        os.system("clear")

        print(f"{self.alias} is currently at ({self.x}, {self.y})", end = "\n\n")
        for i in range(20):
            for j in range(20):
                if {"x": j, "y": i} in drone_list:
                    print("*", end = " ")
                else:
                    print(".", end = " ")
            print()

def get_direction(a, b):
    d = b - a

    if d > 0:
        return 1
    if d < 0:
        return -1
    return 0

def get_partition_number(topic):
    consumer = kafka.KafkaConsumer(
        bootstrap_servers = [BROKER_ADRESS]
    )
    return len(consumer.partitions_for_topic(topic))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <identifier> <alias>")
        quit()

    drone = Drone(int(sys.argv[1]), str(sys.argv[2]))
    print(f"Successfully created drone <{drone.alias}> with identifier <{drone.identifier}>", end = "\n\n")

    threading.Thread(target = drone.get_drone_list, args = None).start()
    threading.Thread(target = drone.get_target, args = None).start()

    # try:
    #     print(f"Registering drone at {REGISTRY_ADRESS[0]}:{REGISTRY_ADRESS[1]}")
    #
    #     if drone.identity_register():
    #         print(f"Received token <{drone.token}>")
    #     else:
    #         print(f"Error in registry, finishing program")
    #         quit()
    # except Exception as e:
    #     print(str(e))
    #     quit()

    # try:
    #     if input("Connect to engine? (y/N) ") is "y":
    #         drone.main_loop(BROKER_ADRESS[0], BROKER_ADRESS[1])
    #     else:
    #         quit()
    # except Exception as e:
    #     print(str(e))
    #     quit()



