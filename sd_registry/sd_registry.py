import socket
import json
import threading
import uuid
import sqlite3

HOST = "localhost"
PORT = 9020
DATA = "registry.db"

class Database:
    def __init__(self):
        pass

    def get_drone(self, identifier) -> dict:
        try:
            with sqlite3.connect(DATA) as con:
                result = con.cursor().execute(f"SELECT * FROM Registry WHERE identifier = {identifier};").fetchone()

                if result is None:
                    return None
                return {
                    "identifier": result[0],
                    "alias": result[1],
                    "token": result[2]
                }
        except Exception as e:
            raise e

    def delete_drone(self, identifier) -> bool:
        try:
            with sqlite3.connect(DATA) as con:
                cur = con.cursor()
                cur.execute(f"DELETE FROM Registry WHERE identifier = {identifier};")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            raise e

    def insert_drone(self, identifier, alias, token) -> bool:
        try:
            with sqlite3.connect(DATA) as con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO Registry (identifier, alias, token) VALUES ({identifier}, '{alias}', '{token}');")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            raise e

    def modify_drone(self, identifier, alias, token) -> bool:
        try:
            with sqlite3.connect(DATA) as con:
                cur = con.cursor()
                cur.execute(f"UPDATE Registry SET alias = '{alias}', token = '{token}' WHERE identifier = {identifier};")
                con.commit()
                return cur.rowcount > 0
        except Exception as e:
            raise e

class Registry:
    def __init__(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((HOST, PORT))
            self.socket.listen(5)
            print(f"Registry server listening on {HOST}:{PORT}")
        except Exception as e:
            raise e

        self.database = Database()
        self.lock = threading.Lock()

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
            data = client_socket.recv(1024).decode("utf-8").loads()
            status = False
            token = None

            print(f"Request received from {client_adress}")

            try:
                if data["operation"] == "register":
                    # Registrar a un nuevo dron
                    if database.insert_drone(data["identifier"], data["alias"], data["token"]):
                        token = str(uuid.uuid4())
                        status = True
                elif data["operation"] == "delete":
                    # Borrar un dron existente
                    status = database.delete_drone(data["identifier"])
                elif data["operation"] == "modify":
                    # Modificar un dron existente
                    status = database.modify_drone(data["identifier"], data["alias"], data["token"])

                response = {
                    "accepted": status,
                    "token": token
                }
                client_socket.send(json.dumps(response).encode("utf-8"))
                client.socket.close()

            except Exception as e:
                raise e

if __name__ == "__main__":
    registry = Registry().start()
