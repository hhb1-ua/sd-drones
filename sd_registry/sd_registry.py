import json
import uuid
import sqlite3
import hashlib
import datetime
import flask

SETTINGS = None
DATABASE = None
REGISTRY = flask.Flask(__name__)

class Database:
    def __init__(self, path):
        self.path = path

    def insert_drone(self, identifier, alias, password):
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

    def insert_token(self, token, expiration):
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

@REGISTRY.route("/register_drone", methods = ["GET", "POST"])
def register_drone():
    try:
        data = flask.request.get_json()

        if SETTINGS["debug"]:
            print(f"Drone registry request with data ({data['identifier']}, {data['alias']}, {data['password']})")

        if data["identifier"] is not None and data["alias"] is not None and data["password"] is not None:
            if DATABASE.insert_drone(data["identifier"], data["alias"], data["password"]):
                return flask.jsonify({}), 200
        return flask.jsonify({}), 400
    except Exception as e:
        return flask.jsonify({}), 400

@REGISTRY.route("/request_token", methods = ["GET", "POST"])
def request_token():
    try:
        data = flask.request.get_json()

        if SETTINGS["debug"]:
            print(f"Token request with data ({data['identifier']}, {data['password']})")

        if DATABASE.validate_drone(data["identifier"], data["password"]):
            token = str(uuid.uuid4())
            expiration = datetime.datetime.now() + datetime.timedelta(0, SETTINGS["registry"]["expiration"])
            if DATABASE.insert_token(token, expiration):
                return flask.jsonify({"token": token}), 200
        return flask.jsonify({}), 400
    except Exception as e:
        return flask.jsonify({}), 400


if __name__ == "__main__":
    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down")
        quit()

    try:
        DATABASE = Database(SETTINGS["registry"]["database"])
        REGISTRY.run(
            host = SETTINGS["address"]["registry"]["host"],
            port = SETTINGS["address"]["registry"]["port"],
            ssl_context = (SETTINGS["registry"]["certificate"], SETTINGS["registry"]["key"]) if SETTINGS["registry"]["secure"] else None)
    except Exception as e:
        raise e
        print("Service stopped abruptly, shutting down")
        quit()
