import socket
import json
import threading
import uuid
import sqlite3

# GENERAR UUID:
# str(uuid.uuid4())

HOST = "localhost"
PORT = 9020
DATA = "registry.db"

class Server:
    def __init__(self):
        pass

    def handle_request(self):
        pass

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
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((HOST, PORT))
            self.server.listen(5)
        except Exception as e:
            raise e

        self.lock = threading.Lock()

    def handle_request():
        socket, adress = self.server.accept()
        with self.lock:
            data = socket.recv(2048).decode("utf-8").loads()
        socket.close()

    def drone_exists(identifier):
        pass


