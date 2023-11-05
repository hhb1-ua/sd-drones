import json
import socket
import sys
import os
import kafka

ENGINE_ADRESS = ("engine", 9010)
REGISTRY_ADRESS =  ("registry", 9020)
BROKER_ADRESS =  ("kafka", 9092)
CONNECTION_TIMEOUT = 20

class Listener:
    def __init__(self, partition)
        """
        :partition:     Partición de escucha
        :timestamp:     Hora de la última trama recibida
        :status:        Estado de la conexión
        :identifier:    Identificador externo
        :position:      Posición actual
        :target:        Posición final
        """
        self.partition = partition
        self.timestamp = None
        self.status = True
        self.identifier = None
        self.position = None
        self.target = None

class AuthenticationServer:
    def __init__(self):


    def start(self):
        try:
            while True:
                self.handle_request()
        except Exception as e:
            self.socket.close()
            raise e

    def handle_request(self):
        client_socket, client_adress = self.socket.accept()

        with self.lock:
            data = json.loads(client_socket.recv(1024).decode("utf-8"))
            status = False
            token = None

            print(f"Request received from {client_adress[0]}:{client_adress[1]}")

            try:
                if data["operation"] == "register":
                    # Registrar a un nuevo dron
                    token = str(uuid.uuid4())
                    if self.database.insert_drone(data["identifier"], data["alias"], token):
                        status = True
                elif data["operation"] == "delete":
                    # Borrar un dron existente
                    status = self.database.delete_drone(data["identifier"])
                elif data["operation"] == "modify":
                    # Modificar un dron existente
                    status = self.database.modify_drone(data["identifier"], data["alias"])

                response = {
                    "accepted": status,
                    "token": token
                }
                client_socket.send(json.dumps(response).encode("utf-8"))
                client_socket.close()

            except Exception as e:
                raise e

class Engine:
    def __init__(self):
        self.listeners = {} # Diccionario que relaciona la llave de objetivo del dron con su información
        self.unasigned = [] # Lista de llaves de objetivo que aún no han sido asignadas
        self.socket = None
        self.lock = None
        self.auth = False

    def add_listener(self, key, listener):
        if self.listeners.has_key(key):
            return False

        self.listeners[key] = listener
        return True

    def initialize_authentication_service(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(ENGINE_ADRESS)
            self.socket.listen(5)
        except Exception as e:
            raise e

        self.lock = threading.Lock()
        self.auth = True

        while self.auth:
            authentication_service()

    def authentication_service(self):
        client_socket, client_adress = self.socket.accept()

        with self.lock:
            data = json.loads(client_socket.recv(1024).decode("utf-8"))
            status = False
            token = None

            print(f"Request received from {client_adress[0]}:{client_adress[1]}")

            try:
                if validate_token(data["token"]):
                    status = True

                client_socket.send(json.dumps({"accepted": status}).encode("utf-8"))
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

    def track_drones(self):
        consumer = kafka.KafkaConsumer(
            "drone_position",
            bootstrap_servers = [f"{BROKER_ADRESS[0]}:{BROKER_ADRESS[1]}"],
            value_deserializer = lambda msg: msg.decode("utf-8"),
            consumer_timeout_ms = CONNECTION_TIMEOUT * 1000
        )

        for message in consumer:
            content = json.loads(message.value)

            print(f"Received message from drone {content["alias"]} with identifier {content["identifier"]} at partition {message.partition}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print()
        quit()

    try:
        engine = new Engine()
    except Exception as e:
        print(str(e))
