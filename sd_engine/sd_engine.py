import json
import socket
import sys
import os
import kafka
import datetime
import threading
import time
import sqlite3
import hashlib
import flask
import requests
from cryptography.fernet import Fernet

SETTINGS        = None
REGISTRY        = None
AUDITORY        = None
PERSIST         = None
ENGINE          = None
AUTHENTICATE    = flask.Flask(__name__)

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
                figure_list.append(figure)
            return figure_list
    except Exception as e:
        return None

class RegistryDatabase:
    def __init__(self, path):
        self.path = path

    def validate_drone(self, identifier, password):
        password = hashlib.sha256(bytes(password, SETTINGS["message"]["codification"])).hexdigest()
        try:
            with sqlite3.connect(self.path) as con:
                return con.cursor().execute(f"SELECT * FROM Drone WHERE identifier = {identifier} AND password = '{password}';").fetchone() is not None
        except Exception as e:
            print(str(e))
            return False

    def validate_token(self, token):
        try:
            with sqlite3.connect(self.path) as con:
                query = con.cursor().execute(f"SELECT * FROM Token WHERE token = '{token}';").fetchone()
                if query is not None:
                    if datetime.datetime.now() < datetime.datetime.strptime(query[1], "%Y-%m-%d %H:%M:%S.%f"):
                        return True
                return False
        except Exception as e:
            print(str(e))
            return False

class PersistDatabase:
    def __init__(self, path):
        self.path = path

    def save_data(self, figure, queue, listeners, safe):
        try:
            drones = {}
            for key in listeners:
                drones[key] = listeners[key].to_dict()
            with open(self.path, "w") as data:
                data.write(json.dumps({
                    "figure": figure,
                    "queue": queue,
                    "drones": drones,
                    "safe": safe}))
            return True
        except Exception as e:
            print(str(e))
            return False

    def load_data(self):
        try:
            with open(self.path, "r") as backup:
                data = json.loads(backup.read())

                data["listeners"] = {}
                for key in data["drones"]:
                    listener = Listener()
                    listener.from_dict(data["drones"][key])
                    data["listeners"][int(key)] = listener
                del data["drones"]

                return data
        except Exception as e:
            print(str(e))
            return None

class AuditoryDatabase:
    def __init__(self, path):
        self.path = path

    def get_total_rows(self):
        try:
            with sqlite3.connect(self.path) as con:
                return con.cursor().execute("SELECT count(*) FROM Auditory;").fetchone()[0]
        except Exception as e:
            return None

    def commit_log(self, timestamp, action, description):
        try:
            identifier = self.get_total_rows()
            if identifier is None:
                return False

            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO Auditory (identifier, stamp, action, description) VALUES ({identifier}, '{stamp}', '{action}', '{description}');")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(str(e))
            return False

class Figure:
    def __init__(self, name = ""):
        self.name   = name
        self.drones = {}

    def add_drone(self, identifier, position):
        if self.drones.get(identifier) is not None:
            return False
        self.drones[int(identifier)] = position
        return True

    def to_dict(self):
        return {"name": self.name, "drones": self.drones}

    def from_dict(self, figure):
        self.name = figure["name"]
        for key in figure["drones"]:
            self.add_drone(int(key), figure["drones"][key])

        return self

class Listener:
    def __init__(self, crypto):
        # Información del dron
        self.position   = {"x": 0, "y": 0}

        # Información de escucha
        self.timestamp  = None
        self.crypto     = crypto
        self.alive      = True
        self.active     = False
        self.positioned = False
        self.usable     = True

        self.stamp()

    def stamp(self):
        self.timestamp = datetime.datetime.now()

    def finalized(self):
        return self.positioned or not self.alive or not self.active

    def to_dict(self):
        return {
            "position": self.position,
            "alive": self.alive,
            "active": self.active,
            "positioned": self.positioned}

    def from_dict(self, listener):
        self.position = listener["position"]
        self.alive = listener["alive"]
        self.active = listener["active"]
        self.positioned = listener["positioned"]

class Engine:
    def __init__(self, database_registry, database_persist, reload_backup = False):
        self.figure     = None
        self.queue      = []
        self.listeners  = {}

        # Bases de datos
        self.database_registry   = database_registry
        self.database_persist    = database_persist

        # Servicio de clima
        self.safe   = True

        # Servicios activos
        self.service_authentication = False
        self.service_weather        = False
        self.service_spectacle      = False
        self.service_removal        = False

        self.set_partitions("drone_position", SETTINGS["broker"]["partitions"])
        self.set_partitions("drone_target", SETTINGS["broker"]["partitions"])
        self.set_partitions("drone_list", 1)

        # Recargar información previa
        if reload_backup:
            data = self.database_persist.load_data()

            self.figure     = Figure().from_dict(data["figure"]) if data["figure"] is not None else None
            self.queue      = list(map(lambda x: Figure().from_dict(x), data["queue"]))
            self.listeners  = data["listeners"]
            self.safe       = data["safe"]

        threading.Thread(target = self.start_weather_service, args = ()).start()
        # threading.Thread(target = self.start_removal_service, args = ()).start()
        # threading.Thread(target = self.start_spectacle_service, args = ()).start()

    def start_spectacle_service(self):
        BROKER_ADRESS = SETTINGS["adress"]["broker"]["host"] + ":" + str(SETTINGS["adress"]["broker"]["port"])

        producer = kafka.KafkaProducer(
            bootstrap_servers = [BROKER_ADRESS],
            value_serializer = lambda msg: json.dumps(msg).encode(SETTINGS["message"]["codification"]))

        threading.Thread(target = self.track_drone_position, args = ()).start()

        self.service_spectacle = True
        while self.service_spectacle:
            print("\033c", end = "")

            # Leer el archivo de figuras
            if self.figure is None and len(self.queue) == 0:
                print("Awaiting for 'figures.json' file")
                figures = get_figures(SETTINGS["engine"]["figures"])
                if figures is not None:
                    self.queue = figures
                self.publish_drone_target(producer)
            # Ejecutar las figuras
            else:
                # Avanzar en la cola
                if self.figure is None:
                    self.figure = self.queue.pop(0)

                    for key in self.listeners:
                        if self.figure.drones.get(key) is not None:
                            self.listeners[key].active = True
                        else:
                            self.listeners[key].active = False

                self.publish_drone_list(producer)
                self.publish_drone_target(producer)

                # Imprimir mapa e información
                print(f"Printing figure <{self.figure.name}>")
                print(str(self))

                # Comprobar si la figura ha acabado
                finished = True
                for key in self.listeners:
                    if not self.listeners[key].finalized():
                        finished = False
                        break
                if finished:
                    self.figure = None

            # Imprimir el estado del clima
            weather = "SAFE"
            if not self.safe:
                weather = "DANGEROUS"
            if not self.alive:
                weather = "UNKNOWN"
            print(f"Weather status: {weather}")

            # Imprimir la lista de drones
            for key in self.listeners:
                listener = self.listeners[key]

                status = "ALIVE"
                if not listener.alive:
                    status = "DEAD"

                key = fill_left(str(key), 2)
                p_x = fill_left(str(listener.position["x"]), 2)
                p_y = fill_left(str(listener.position["y"]), 2)

                print(f"<{key}> ({p_x}, {p_y}) {status}")

            # Hacer una copia de seguridad
            self.database_persist.save_data(
                self.figure.to_dict() if self.figure != None else None,
                list(map(lambda x: x.to_dict(), self.queue)),
                self.listeners,
                self.safe)

            time.sleep(SETTINGS["engine"]["tick"])

    def publish_drone_list(self, producer):
        producer.send("drone_list", value = {"map": str(self)})

    def publish_drone_target(self, producer):
        for key in self.listeners:
            target = {"x": 0, "y": 0}

            if not self.figure is None and self.safe:
                if self.listeners[key].active:
                    if self.figure.drones.get(key) is not None:
                        target = self.figure.drones[key]

            producer.send("drone_target", value = target, partition = key)

    def track_drone_position(self):
        consumer = kafka.KafkaConsumer(
            "drone_position",
            bootstrap_servers = [SETTINGS["adress"]["broker"]["host"] + ":" + str(SETTINGS["adress"]["broker"]["port"])],
            value_deserializer = lambda msg: json.loads(msg.decode(SETTINGS["message"]["codification"])))

        for message in consumer:
            listener_key = message.value["identifier"]

            if self.listeners.get(listener_key) is not None:
                self.listeners[listener_key].stamp()
                self.listeners[listener_key].position = message.value["position"]

                if self.figure is not None and self.listeners[listener_key].active:
                    self.listeners[listener_key].positioned = message.value["position"] == self.figure.drones[listener_key]
                else:
                    self.listeners[listener_key].positioned = False

    def add_listener(self, key, listener):
        if self.listeners.get(key) is not None:
            return False
        self.listeners[key] = listener
        return True

class AdvancedEngine:
    def __init__(self, persist, auditory):
        self.figure = None
        self.queue = []
        self.listeners = {}
        self.persist = persist
        self.auditory = auditory
        self.safe = True

        # Servicios activos
        self.service_weather = False
        self.service_spectacle = False
        self.service_removal = False

        # Productores y consumidores de Kafka
        self.producer = kafka.KafkaProducer(
            bootstrap_servers = [str(SETTINGS["address"]["broker"]["host"]) + ":" + str(SETTINGS["address"]["broker"]["port"])])
        self.consumer = kafka.KafkaConsumer(
            "drone_position",
            bootstrap_servers = [SETTINGS["address"]["broker"]["host"] + ":" + str(SETTINGS["address"]["broker"]["port"])])

    def run_services(self):
        if not self.service_weather:
            threading.Thread(target = self.start_weather_service, args = ()).start()

        if not self.service_removal:
            threading.Thread(target = self.start_removal_service, args = ()).start()

        if not self.service_spectacle:
            threading.Thread(target = self.start_spectacle_service, args = ()).start()

    def start_weather_service():
        self.service_weather = True
        while self.service_weather:
            try:
                with open(SETTINGS["engine"]["weather"], "r") as source:
                    data = json.loads(source.read())
                    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={data['city']}&appid={data['key']}")
                    temperature = response.json()["main"]["temp"]
                    self.safe = temperature >= SETTINGS["weather"]["threshold"]
                    if SETTINGS["debug"]:
                        print(f"Read {temperature}ºK, weather safety set to {self.safe}")
            except Exception as e:
                if SETTINGS["debug"]:
                    print("Error when connecting to OpenWeather")
            finally:
                time.sleep(SETTINGS["engine"]["tick"])

    def start_removal_service(self):
        self.service_removal = True
        while self.service_removal:
            current_time = datetime.datetime.now()

            for key in self.listeners:
                time_elapsed = (current_time - self.listeners[key].timestamp).total_seconds()

                if self.listeners[key].alive:
                    if time_elapsed > SETTINGS["message"]["timeout"]:
                        print(f"Connection lost to drone with identifier <{key}>")
                        self.listeners[key].alive = False
                else:
                    if time_elapsed <= SETTINGS["message"]["timeout"]:
                        print(f"Connection established to drone with identifier <{key}>")
                        self.listeners[key].alive = True

            time.sleep(SETTINGS["engine"]["tick"])

    def start_spectacle_service(self):
        threading.Thread(target = self.track_drone_position, args = ()).start()

        self.service_spectacle = True
        while self.service_spectacle:
            # Limpiar pantalla
            print("\033c", end = "")

            # Leer el archivo de figuras
            if self.figure is None and len(self.queue) == 0:
                print("Awaiting for 'figures.json' file")
                figures = get_figures(SETTINGS["engine"]["figures"])
                if figures is not None:
                    self.queue = figures
                self.publish_drone_target(producer)

            # Ejecutar las figuras
            else:
                # Avanzar en la cola
                if self.figure is None:
                    self.figure = self.queue.pop(0)

                    for key in self.listeners:
                        if self.figure.drones.get(key) is not None:
                            self.listeners[key].active = True
                        else:
                            self.listeners[key].active = False

                self.publish_drone_list()
                self.publish_drone_target()

                # Imprimir mapa e información
                print(f"Printing figure <{self.figure.name}>")
                print(str(self))

                # Comprobar si la figura ha acabado
                finished = True
                for key in self.listeners:
                    if not self.listeners[key].finalized():
                        finished = False
                        break
                if finished:
                    self.figure = None

            # Imprimir el estado del clima
            weather = "SAFE"
            if not self.safe:
                weather = "DANGEROUS"
            print(f"Weather status: {weather}")

            # Imprimir la lista de drones
            for key in self.listeners:
                listener = self.listeners[key]

                status = "ALIVE"
                if not listener.alive:
                    status = "DEAD"
                if not listener.usable:
                    status = "CORRUPTED"

                key = str(key)
                p_x = str(listener.position["x"])
                p_y = str(listener.position["y"])
                print(f"<{key}> ({p_x}, {p_y}) {status}")

            # Hacer una copia de seguridad
            self.persist.save_data(
                self.figure.to_dict() if self.figure != None else None,
                list(map(lambda x: x.to_dict(), self.queue)),
                self.listeners,
                self.safe)

            time.sleep(SETTINGS["engine"]["tick"])

    def add_listener(self, identifier):
        data = {
            "crypto": None,
            "position": {
                "x": 0,
                "y": 0
            }
        }

        if self.listeners.get(identifier) is None:
            crypto = Fernet.generate_key()
            self.listeners[identifier] = Listener(crypto)
            data["crypto"] = crypto.decode()

            # Activar el dron
            if self.figure is not None:
                if self.figure.drones.get(identifier) is not None:
                    self.listeners[identifier].active = True
        else:
            data["crypto"] = self.listeners[identifier].crypto.decode()
            data["position"] = self.listeners[identifier].position

        return data

    def publish_drone_target(self):
        for key in self.listeners:
            fernet = Fernet(self.listeners[key].crypto)
            target = {"x": 0, "y": 0}

            if self.figure is not None and self.safe:
                if self.listeners[key].active:
                    if self.figure.drones[key] is not None:
                        target = self.figure.drones[key]

            self.producer.send(
                "drone_target",
                value = fernet.encrypt(json.dumps(target).encode(SETTINGS["message"]["codification"])),
                partition = key)

    def publish_drone_list(self):
        for key in self.listeners:
            fernet = Fernet(self.listeners[key].crypto)
            self.producer.send(
                "drone_list",
                value = fernet.encrypt(json.dumps({"map": str(self)}).encode(SETTINGS["message"]["codification"])),
                partition = key)

    def track_drone_position(self):
        for message in self.consumer:
            key = message.partition

            if self.listeners[key] is not None:
                fernet = Fernet(self.listeners[key].crypto)

                try:
                    data = json.loads(fernet.decrypt(message).decode(SETTINGS["message"]["codification"]))

                    self.listeners[key].stamp()
                    self.listeners[key].position = data["position"]

                    if self.figure is not None and self.listeners[key].active:
                        self.listeners[key].positioned = data["position"] == self.figure.drones[key]
                    else:
                        self.listeners[key].positioned = False
                except Exception as e:
                    # Los datos no se pueden desencriptar
                    self.listeners[key].active = False
                    self.listeners[key].usable = False

    def get_partitions(self, topic):
        try:
            return len(self.consumer.partitions_for_topic(topic))
        except:
            return None

    def set_partitions(self, topic, number):
        admin = kafka.KafkaAdminClient(
            bootstrap_servers = [SETTINGS["address"]["broker"]["host"] + ":" + str(SETTINGS["address"]["broker"]["port"])])
        current_partitions = self.get_partitions(topic)

        if current_partitions is None:
            admin.create_topics(new_topics = [kafka.admin.NewTopic(name = topic, num_partitions = number, replication_factor = 1)])
        elif current_partitions != number:
            admin.create_partitions({topic: kafka.admin.new_partitions.NewPartitions(number)})

    def get_colored_positions(self):
        positions = {}

        for key in self.listeners:
            listener = self.listeners[key]
            position = f"{listener.position['x']}.{listener.position['y']}"

            # Ignorar los drones fuera de uso
            if not listener.active:
                continue
            # Marcar los drones muertos como grises
            if not listener.alive:
                if not position in positions:
                    positions[position] = 0
                continue
            # Marcar los drones en movimiento como rojos
            if not listener.positioned:
                if not position in positions:
                    positions[position] = 1
                continue
            # Marcar los drones posicionados como verdes
            positions[position] = 2

        return positions

    def __str__(self):
        positions = self.get_colored_positions()
        result = ""

        for i in range(SETTINGS["map"]["rows"]):
            for j in range(SETTINGS["map"]["cols"]):
                key = f"{j}.{i}"

                if key in positions:
                    match positions[key]:
                        case 0:
                            result += "\033[37m*\033[0m "
                        case 1:
                            result += "\033[31m*\033[0m "
                        case 2:
                            result += "\033[32m*\033[0m "
                        case _:
                            result += "? "
                else:
                    result += ". "
            result += "\n"

        return result


@AUTHENTICATE.route("/authenticate_drone", methods = ["GET", "POST"])
def authenticate_drone():
    try:
        data = flask.request.get_json()

        if SETTINGS["debug"]:
            print(f"Drone authentication request with data ({data['identifier']}, {data['password']}, {data['token']})")

        if data["identifier"] is not None and data["password"] is not None and data["token"] is not None:
            if REGISTRY.validate_drone(data["identifier"], data["password"]) and REGISTRY.validate_token(data["token"]):
                data = ENGINE.add_listener(data["identifier"])
                print(data)
                return flask.jsonify(data), 200
            else:
                print("Validation error")
        else:
            print("Data error")
        return flask.jsonify({}), 400
    except Exception as e:
        raise e
        return flask.jsonify({}), 400

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <reload>")
        quit()

    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down")
        quit()

    REGISTRY = RegistryDatabase(SETTINGS["engine"]["registry"])
    PERSIST = PersistDatabase(SETTINGS["engine"]["persist"])
    AUDITORY = AuditoryDatabase(SETTINGS["engine"]["auditory"])

    if int(sys.argv[1]) == 1:
        print("Reloading persist...")
        ENGINE = AdvancedEngine(PERSIST, AUDITORY)
    else:
        ENGINE = AdvancedEngine(PERSIST, AUDITORY)

    ENGINE.set_partitions("drone_position", SETTINGS["broker"]["partitions"])
    ENGINE.set_partitions("drone_target", SETTINGS["broker"]["partitions"])
    ENGINE.set_partitions("drone_list", SETTINGS["broker"]["partitions"])
    # ENGINE.run_services()

    AUTHENTICATE.run(
        host = SETTINGS["address"]["authenticate"]["host"],
        port = SETTINGS["address"]["authenticate"]["port"],
        ssl_context = (SETTINGS["engine"]["certificate"], SETTINGS["engine"]["key"]) if SETTINGS["engine"]["secure"] else None)
