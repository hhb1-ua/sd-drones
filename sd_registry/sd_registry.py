import socket
import json
import threading
import uuid
import sqlite3
import hashlib
import datetime
import flask

# HACK
# datetime.datetime.now() + datetime.timedelta(0, SECONDS)

SETTINGS = None
REGISTRY = None

class Database:
    def __init__(self, path):
        self.path = path

    def create_drone(self, identifier, alias, password):
        password = hashlib.sha256(bytes(password, SETTINGS["message"]["codification"])).hexdigest()
        try:
            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO Drone (identifier, alias, password) VALUES ({identifier}, '{alias}', '{password}');")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(str(e))
            return False

    def validate_drone(self, identifier, password):
        password = hashlib.sha256(bytes(password, SETTINGS["message"]["codification"])).hexdigest()
        try:
            with sqlite3.connect(self.path) as con:
                return con.cursor().execute(f"SELECT * FROM Drone WHERE identifier = {identifier} AND password = '{password}';").fetchone() is not None
        except Exception as e:
            print(str(e))
            return False

    def create_token(self, token, expiration):
        try:
            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO Token (token, expiration) VALUES ('{token}', '{expiration}');")
                con.commit()
                return cur.rowcount > 0
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

class Registry:
    def __init__(self, database):
        self.database   = database
        self.service    = False

        try:
            threading.Thread(target = self.start_service, args = ()).start()
        except Exception as e:
            raise e

    def start_service(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SETTINGS["adress"]["registry"]["host"], SETTINGS["adress"]["registry"]["port"]))
        server_socket.listen(SETTINGS["registry"]["backlog"])

        self.service = True
        while self.service:
            client_socket, client_adress = server_socket.accept()
            print(f"Request received from drone at {client_adress[0]}:{client_adress[1]}")
            try:
                self.handle_request(client_socket)
            except Exception as e:
                print(f"The request couldn't be handled properly ({str(e)})")

    def handle_request(self, client_socket):
        with threading.Lock() as lock:
            data    = json.loads(client_socket.recv(SETTINGS["message"]["length"]).decode(SETTINGS["message"]["codification"]))
            status  = False
            token   = None

            if data["operation"] == "register":
                # Registrar a un nuevo dron
                token = str(uuid.uuid4())
                if self.database.insert_drone(data["identifier"], data["alias"], token):
                    status = True
                    print(f"Sent token <{token}> to drone <{data['alias']}>")
            elif data["operation"] == "delete":
                # Borrar un dron existente
                status = self.database.delete_drone(data["identifier"])
            elif data["operation"] == "modify":
                # Modificar un dron existente
                status = self.database.modify_drone(data["identifier"], data["alias"])

            response = json.dumps({
                "accepted": status,
                "token": token})
            client_socket.send(response.encode(SETTINGS["message"]["codification"]))
            client_socket.close()

if __name__ == "__main__":
    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down")
        quit()

    try:
        REGISTRY = Registry(Database(SETTINGS["registry"]["database"]))
        print("Registry server has been successfully started")
    except Exception as e:
        raise e
        print("Service stopped abruptly, shutting down")
        quit()
