import socket
import json
import threading
import uuid
import sqlite3

SETTINGS = None
REGISTRY = None

class Database:
    def __init__(self, path):
        self.path = path

    def get_drone(self, identifier):
        try:
            with sqlite3.connect(self.path) as con:
                result = con.cursor().execute(f"SELECT * FROM Registry WHERE identifier = {identifier};").fetchone()

                if result is None:
                    return None
                return {
                    "identifier": result[0],
                    "alias": result[1],
                    "token": result[2]
                }
        except Exception as e:
            print(str(e))
            return None

    def delete_drone(self, identifier):
        try:
            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute(f"DELETE FROM Registry WHERE identifier = {identifier};")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(str(e))
            return False

    def insert_drone(self, identifier, alias, token):
        try:
            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO Registry (identifier, alias, token) VALUES ({identifier}, '{alias}', '{token}');")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(str(e))
            return False

    def modify_drone(self, identifier, alias):
        try:
            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute(f"UPDATE Registry SET alias = '{alias}' WHERE identifier = {identifier};")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(str(e))
            return False

    def validate_drone(self, identifier, token):
        try:
            with sqlite3.connect(self.path) as con:
                return not con.cursor().execute(f"SELECT * FROM Registry WHERE identifier = {identifier} AND token = {token};").fetchone() is None
        except Exception as e:
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
        print("Service stopped abruptly, shutting down")
        quit()
