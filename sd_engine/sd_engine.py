import json
import socket
import sys
import os
import kafka
import datetime
import threading

ENGINE_ADRESS           = ("engine", 9010)
ENGINE_WEATHER_ADRESS   = ("engine", 9011)
REGISTRY_ADRESS         = ("registry", 9020)
BROKER_ADRESS           = ("kafka", 9092)
CONNECTION_TIMEOUT      = 20

def read_figure_file(source):
    figures = []
    with open(source, "r") as _file:
        raw = json.loads(_file.read())
        for f in raw["figuras"]:
            figure = {}
            figure["name"] = f["Nombre"]
            figure["drones"] = []
            for d in f["Drones"]:
                coords = d["POS"].split(",")
                figure["drones"].push({"identifier": d["ID"], "target": {"x": coords[0], "y": coords[1]}})
    return figures

class Listener:
    def __init__(self, partition):
        """
        :partition:     Partición de escucha
        :timestamp:     Hora de la última trama recibida
        :status:        Estado de la conexión
        :identifier:    Identificador externo
        :position:      Posición actual
        :target:        Posición final
        """
        self.partition  = partition
        self.timestamp  = None
        self.status     = True
        self.identifier = None
        self.position   = None
        self.target     = None

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
        client_socket, client_adress = drone_socket.accept()
        lock = threading.Lock()

        with lock:
            data = json.loads(client_socket.recv(1024).decode("utf-8"))
            status = False
            partition = 0
            print(f"Request received from {client_adress[0]}:{client_adress[1]}")

            try:
                if validate_token(data["token"]):
                    status = True
                    asigned_target = self.unasigned.pop()
                    partition = asigned_target["key"]
                    self.add_listener()

                client_socket.send(json.dumps({"accepted": status, "partition": partition}).encode("utf-8"))
                client_socket.close()
            except Exception as e:
                print(str(e))

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
    engine = Engine()

    threading.Thread(target = engine.initialize_authentication_service, args = None).start()
    threading.Thread(target = engine.initialize_engine_service, args = None).start()

    print("Hello world?")
