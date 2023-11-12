# TODO: Base de datos de persistencia

import json
import socket
import sys
import os
import kafka
import datetime
import threading
import time

SETTINGS    = None
ENGINE      = None

def get_figures(path):
    try:
        with open(path, "r") as figure_file:
            figure_data = json.loads(figure_file.read())
            figure_list = []
            for f in figure_data["figuras"]:
                figure = Figure(f["Nombre"])
                for drone in f["Drones"]:
                    t = drone["POS"].split(",")
                    target = {"x": int(t[0]), "y": int(t[1])}
                    figure.add_drone(int(drone["ID"]), target)
            return figure_list
    except Exception as e:
        return None

class RegistryDatabase:
    def __init__(self, path):
        self.path = path

    def validate_drone(self, identifier, token):
        try:
            with sqlite3.connect(self.path) as con:
                return not con.cursor().execute(f"SELECT * FROM Registry WHERE identifier = {identifier} AND token = {token};").fetchone() is None
        except Exception as e:
            print(str(e))
            return False

class PersistDatabase:
    def __init__(self, path):
        self.path = path

class Figure:
    def __init__(self, name):
        self.name   = name
        self.drones = {}

    def add_drone(identifier, position):
        if self.drones.has_key(identifier):
            return False
        self.drones[identifier] = position
        return True

class Listener:
    def __init__(self):
        # Información del dron
        self.position   = None

        # Información de escucha
        self.timestamp  = None
        self.alive      = True
        self.active     = False
        self.positioned = False

        self.stamp()

    def stamp(self):
        self.timestamp = datetime.datetime.now()

    def finalized(self):
        return self.alive and self.active and self.positioned

class Engine:
    def __init__(self, database_registry, database_persist):
        self.figure     = None
        self.queue      = []
        self.listeners  = {}
        self.safe       = True

        # Bases de datos
        self.database_registry   = database_registry
        self.database_persist    = database_persist

        # Servicios activos
        self.service_authentication = False
        self.service_weather        = False
        self.service_spectacle      = False
        self.service_removal        = False

        # if self.get_partitions("drone_position") < SETTINGS["engine"]["partitions"]:
        #     self.add_partitions("drone_position", SETTINGS["engine"]["partitions"])
        #
        # if self.get_partitions("drone_target") < SETTINGS["engine"]["partitions"]:
        #     self.add_partitions("drone_target", SETTINGS["engine"]["partitions"])

        threading.Thread(target = self.start_authentication_service, args = ()).start()
        threading.Thread(target = self.start_weather_service, args = ()).start()
        threading.Thread(target = self.start_removal_service, args = ()).start()
        threading.Thread(target = self.start_spectacle_service, args = ()).start()

    def start_weather_service(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SETTINGS["adress"]["weather"]["host"], SETTINGS["adress"]["weather"]["port"]))
        server_socket.listen(SETTINGS["engine"]["backlog"])

        self.service_weather = True
        while self.service_weather:
            weather_socket, weather_adress = server_socket.accept()
            print(f"Request received from weather server at {weather_adress[0]}:{weather_adress[1]}")
            try:
                with threading.Lock() as lock:
                    self.safe = json.loads(weather_socket.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"]))["safe"]
            except Exception as e:
                print(f"The request couldn't be handled properly ({str(e)})")
            finally:
                weather_socket.close()

    def start_authentication_service(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SETTINGS["adress"]["authentication"]["host"], SETTINGS["adress"]["authentication"]["port"]))
        server_socket.listen(SETTINGS["engine"]["backlog"])

        self.service_authentication = True
        while self.service_authentication:
            drone_socket, drone_adress = server_socket.accept()
            print(f"Request received from drone at {drone_adress[0]}:{drone_adress[1]}")
            try:
                with threading.Lock():
                    data    = json.loads(drone_socket.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"]))
                    status  = False

                    if self.database_registry.validate_drone(data["identifier"], data["token"]):
                        if self.add_listener(data["identifier"], Listener()):
                            status = True
                    drone_socket.send(json.dumps({"accepted": status}).encode(SETTINGS["message"]["codification"]))
            except Exception as e:
                print(f"The request couldn't be handled properly ({str(e)})")
            finally:
                drone_socket.close()

    def start_spectacle_service(self):
        BROKER_ADRESS = SETTINGS["adress"]["broker"]["host"] + ":" + str(SETTINGS["adress"]["broker"]["port"])

        producer = kafka.KafkaProducer(
            bootstrap_servers = [BROKER_ADRESS],
            value_serializer = lambda msg: json.dumps(msg.encode(SETTINGS["message"]["codification"])))

        consumer = kafka.KafkaConsumer(
            "drone_position",
            bootstrap_servers = [BROKER_ADRESS],
            value_deserializer = lambda msg: json.loads(msg.decode(SETTINGS["message"]["codification"])))

        threading.Thread(target = self.consume_drone_position, args = (consumer)).start()

        self.service_spectacle = True
        while self.service_spectacle:
            # Leer el archivo de figuras
            if self.figure is None and len(self.queue) == 0:
                figures = get_figures(SETTINGS["engine"]["figures"])
                if not figures is None:
                    self.queue = figures
            # Ejecutar las figuras
            else:
                # Avanzar en la cola
                if self.figure is None:
                    self.figure = self.queue.pop(0)

                # Publicar información
                self.publish_drone_list(producer)
                self.publish_drone_target(producer)

                # Imprimir mapa
                self.print_map()

                # Comprobar si la figura ha acabado
                finished = True
                for key in self.listeners:
                    if not self.listeners[key].finalized():
                        finished = False
                        break
                if finished:
                    self.figure = None

            time.sleep(SETTINGS["engine"]["tick"])

    def publish_drone_list(self, producer):
        producer.send("drone_list", value = self.listeners)

    def publish_drone_target(self, producer):
        for key in self.listeners:
            target = {"x": 0, "y": 0}

            if not self.figure is None and self.safe:
                if self.listeners[key].active:
                    if self.figure.drones.has_key(key):
                        target = self.figure.drones[key]

            producer.send("drone_target", value = target, partition = key)

    def consume_drone_position(self, consumer):
        for message in consumer:
            listener_key = message.value["identifier"]

            if self.listeners.has_key(listener_key):
                self.listeners[listener_key].stamp()
                self.listeners[listener_key].position = message.value["position"]
                self.listeners[listener_key].positioned = message.value["position"] is self.figure.drones[listener_key].target

    def start_removal_service(self):
        self.service_removal = True
        while self.service_removal:
            current_time = datetime.datetime.now()

            for key in self.listeners:
                time_elapsed = (current_time - self.listeners[key]["timestamp"]).total_seconds()

                if self.listeners[key].alive:
                    if time_elapsed > SETTINGS["message"]["timeout"]:
                        self.listeners[key].alive = False
                else:
                    if time_elapsed <= SETTINGS["message"]["timeout"]:
                        self.listeners[key].alive = True

            time.sleep(SETTINGS["engine"]["tick"])

    def add_listener(self, key, listener):
        if self.listeners.has_key(key):
            return False
        self.listeners[key] = listener
        return True

    def get_partitions(self, topic):
        consumer = kafka.KafkaConsumer(
            bootstrap_servers = [SETTINGS["adress"]["broker"]["host"] + ":" + str(SETTINGS["adress"]["broker"]["port"])])
        return len(consumer.partitions_for_topic(topic))

    def add_partitions(self, topic, number):
        admin = kafka.KafkaAdminClient(
            bootstrap_servers = [SETTINGS["adress"]["broker"]["host"] + ":" + str(SETTINGS["adress"]["broker"]["port"])])
        admin.create_partitions({topic: kafka.admin.new_partitions.NewPartitions(number)})

    def print_map(self):
        pass

if __name__ == "__main__":
    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down")
        quit()

    try:
        ENGINE = Engine(RegistryDatabase(SETTINGS["engine"]["registry"]), PersistDatabase(SETTINGS["engine"]["persist"]))
    except Exception as e:
        print(str(e))
        print("Service stopped abruptly, shutting down")
        quit()
