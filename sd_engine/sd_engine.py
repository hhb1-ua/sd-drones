# TODO: Base de datos de persistencia

import json
import socket
import sys
import os
import kafka
import datetime
import threading

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
    def __init__(self, path)
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
        self.queue      = []
        self.listeners  = {}
        self.safe       = True

        # Bases de datos
        self.database_registry   = database_registry
        self.database_persist    = database_persist

        # Servicios activos
        self.service_authentication = False
        self.service_weather        = False
        self.service_reading        = False
        self.service_spectacle      = False
        self.service_removal        = False

        threading.Thread(target = self.start_authentication_service, args = ()).start()
        threading.Thread(target = self.start_weather_service, args = ()).start()
        threading.Thread(target = self.start_removal_service, args = ()).start()
        threading.Thread(target = self.start_reading_service, args = ()).start()
        # threading.Thread(target = self.start_spectacle_service, args = ()).start()

    def start_weather_service(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SETTINGS["adress"]["weather"]["host"], SETTINGS["adress"]["weather"]["port"]))
        server_socket.listen(SETTINGS["engine"]["backlog"])

        self.service_weather = True
        while self.service_weather:
            weather_socket, weather_adress = weather_socket.accept()
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
                    data    = json.loads(drone_socket.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"])))
                    status  = False

                    if self.database_registry.validate_drone(data["identifier"], data["token"]):
                        if self.add_listener(data["identifier"], Listener())
                            status = True
                    drone_socket.send(json.dumps({"accepted": status}).encode(SETTINGS["message"]["codification"])))
            except Exception as e:
                print(f"The request couldn't be handled properly ({str(e)})")
            finally:
                drone_socket.close()

    def start_spectacle_service(self):
        BROKER_ADRESS = SETTINGS["adress"]["broker"]["host"] + ":" + str(SETTINGS["adress"]["broker"]["port"])

        producer = kafka.KafkaProducer(
            bootstrap_servers = [BROKER_ADRESS],
            value_serializer = lambda msg: msg.encode(SETTINGS["message"]["codification"])))

        consumer = kafka.KafkaConsumer(
            "drone_position",
            bootstrap_servers = [BROKER_ADRESS],
            value_deserializer = lambda msg: msg.decode(SETTINGS["message"]["codification"]))

        # drone_position: Producer(Drone), Consumer(Engine); Posiciones individuales de cada dron
        # drone_target: Producer(Engine), Consumer(Drone); Objetivos individuales de cada dron
        # drone_list: Producer(Engine), Consumer(Drone); Posiciones y estados de todos los drones

        self.service_spectacle = True
        while self.service_spectacle:
            pass

    def start_removal_service(self):
        self.service_removal = True
        while self.service_removal:
            current_time = datetime.datetime.now()

            for key in self.listeners:
                time_elapsed = (current_time - self.listeners[key]["timestamp"]).total_seconds()
                if time_elapsed > SETTINGS["message"]["timeout"]:
                    self.listeners[key].alive = False

            time.sleep(SETTINGS["engine"]["tick"])

    def add_listener(self, key, listener):
        if self.listeners.has_key(key):
            return False
        self.listeners[key] = listener
        return True

class Engine:
    def __init__(self):
        self.listeners  = {}    # Diccionario que relaciona la llave de objetivo del dron con su información
        self.unasigned  = []    # Lista de llaves de objetivo que aún no han sido asignadas
        self.safe       = True  # Estado de seguridad del clima

        # Servicios en ejecución
        self.authenticacion_service = False
        self.weather_service        = False

    def add_listener(self, key, listener):
        if self.listeners.has_key(key):
            return False

        self.listeners[key] = listener
        return True

    def initialize_weather_service(self):
        weather_socket = None

        try:
            weather_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            weather_socket.bind(ENGINE_WEATHER_ADRESS)
            weather_socket.listen(5)
        except Exception as e:
            raise e

        self.weather_service = True
        while self.weather_service:
            self.track_weather(weather_socket)

    def initialize_authentication_service(self):
        drone_socket = None

        try:
            drone_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            drone_socket.bind(ENGINE_ADRESS)
            drone_socket.listen(5)
        except Exception as e:
            raise e

        self.auth = True
        while self.auth:
            self.authenticate_drone(drone_socket)

    def authenticate_drone(self, drone_socket):


    def validate_token(token):
        # TODO
        return True

    def publish_drone_list(self):
        producer = kafka.KafkaProducer(
            bootstrap_servers = [BROKER_ADRESS],
            value_serializer = lambda message: message.encode("utf-8"))

        drone_list = {}
        for key in self.listeners:
            drone_list[self.listeners[key]["identifier"]] = self.listeners[key]["position"]

        producer.send("drone_list", value = json.dumps(drone_list))

    def publish_targets(self):
        producer = kafka.KafkaProducer(
            bootstrap_servers = [BROKER_ADRESS],
            value_serializer = lambda message: message.encode("utf-8"))

        for key in self.listeners:
            producer.send(
                "drone_list",
                value = json.dumps({
                    "x": self.listeners[key]["target"]["x"],
                    "y": self.listeners[key]["target"]["y"]}),
                partition = self.listeners[key]["partition"])

    def delete_listener(self, key):
        if not self.listeners.has_key(key):
            return False
        del self.listeners[key]
        return True

    def delete_dead_drones(self):
        while self.loop:
            for key in self.listeners:
                timer = self.listeners[key]["timestamp"] - datetime.datetime.now()
                if timer.total_seconds() > CONNECTION_TIMEOUT:
                    print(f"Drone {self.listeners[key]['identifier']} has been removed due to a timeout")
                    delete_ilstener(key)
            time.sleep(2)

    def track_weather(self, weather_socket):
        client_socket, client_adress = weather_socket.accept()
        lock = threading.Lock()

        with lock:
            try:
                self.safe = json.loads(weather_socket.recv(1024).decode("utf-8"))["safe"]
                client_socket.close()
            except Exception as e:
                raise e

    def display_drones(self):
        # TODO
        pass

    def track_drones(self):
        consumer = kafka.KafkaConsumer(
            "drone_position",
            bootstrap_servers = [f"{BROKER_ADRESS[0]}:{BROKER_ADRESS[1]}"],
            value_deserializer = lambda msg: msg.decode("utf-8"),
            consumer_timeout_ms = CONNECTION_TIMEOUT * 1000
        )

        for message in consumer:
            key = message.partition
            data = json.loads(message.value)
            timestamp = datetime.strptime(message.timestamp, "%y-%m-%d %H:%M:%S")

            if self.listeners.has_key(key):
                self.listeners[key].timestamp = timestamp
                self.listeners[key].position = data["position"]

    def initialize_engine_service(self):
        # Primero, debemos tener una figura para leer

if __name__ == "__main__":
    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down")
        quit()

    try:
        ENGINE = Engine()
    except Exception as e:
        print(str(e))
        print("Service stopped abruptly, shutting down")
        quit()
