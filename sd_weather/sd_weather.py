import socket
import json
import time
import threading

ENGINE_ADRESS = ("engine", 9011)

class Weather:
    def __init__(self):
        self.threshold      = 0     # Temperatura mínima
        self.safe           = True  # Estado de seguridad
        self.service        = False # Estado del servicio

        # Comenzar servicio
        try:
            threading.Thread(target = self.track_safety_status, args = (2)).start()
        except Exception as e:
            raise e

    def read_weather_database(self, path):
        try:
            with open(path, "r") as database:
                return json.loads(database.read())["temperature"]
        except Exception as e:
            raise e

    def send_weather_status_notification(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect(ENGINE_ADRESS)
            server.send(json.dumps({"safe": self.safe}).encode("utf-8"))
            server.close()
        except Exception as e:
            server.close()
            raise e

        return False

    def track_safety_status(self, tick):
        self.service = True
        try:
            while self.service:
                temperature = read_weather_database("weather.json")
                if self.safe and temperature < self.threshold:
                    # La temperatura ha pasado a estar fuera del umbral
                    self.safe = False
                    self.send_weather_status_notification()
                else if not self.safe and temperature >= self.threshold:
                    # La temperatura ha pasado a estar dentro del umbral
                    self.safe = True
                    self.send_weather_status_notification()
                time.sleep(tick)

        except Exception as e:
            self.service = False
            raise e
