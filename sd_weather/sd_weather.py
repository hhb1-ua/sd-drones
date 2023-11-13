import socket
import json
import time
import threading

SETTINGS    = None
WEATHER     = None

class Weather:
    def __init__(self):
        self.safe       = True  # Estado de seguridad
        self.service    = False # Estado del servicio

        try:
            threading.Thread(target = self.start_service, args = ()).start()
        except Exception as e:
            raise e

    def start_service(self):
        self.service = True

        try:
            while self.service:
                temperature = self.get_temperature()
                notification = False

                if self.safe and temperature < SETTINGS["weather"]["threshold"]:
                    # La temperatura ha pasado a estar fuera del umbral
                    self.safe = False
                    notification = True
                    print("The temperature has become unsafe, sending notification")

                elif not self.safe and temperature >= SETTINGS["weather"]["threshold"]:
                    # La temperatura ha pasado a estar dentro del umbral
                    self.safe = True
                    notification = True
                    print("The temperature is now safe, sending notification")

                timer = 2
                while notification:
                    try:
                        self.send_notification()
                        break
                    except:
                        if timer <= SETTINGS["message"]["timeout"]:
                            print(f"Couldn't send notification, retrying in {timer} seconds...")
                            time.sleep(timer)
                            timer += 2
                        else:
                            print("Connection lost")
                            break

                time.sleep(SETTINGS["weather"]["tick"])
        except Exception as e:
            self.service = False
            raise e

    def set_temperature(self, temperature):
        try:
            with open(SETTINGS["weather"]["database"], "w") as database:
                database.write(json.dumps({"temperature": temperature}))
        except Exception as e:
            raise e

    def get_temperature(self):
        try:
            with open(SETTINGS["weather"]["database"], "r") as database:
                return json.loads(database.read())["temperature"]
        except Exception as e:
            raise e

    def send_notification(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((SETTINGS["adress"]["weather"]["host"], SETTINGS["adress"]["weather"]["port"]))
            server.send(json.dumps({"safe": self.safe}).encode(SETTINGS["message"]["codification"]))
            server.close()
        except Exception as e:
            raise e

if __name__ == "__main__":
    try:
        with open("settings/settings.json", "r") as settings_file:
            SETTINGS = json.loads(settings_file.read())
    except Exception as e:
        print("Could not load settings file 'settings.json', shutting down")
        quit()

    try:
        WEATHER = Weather()
    except Exception as e:
        print("Service stopped abruptly, shutting down")
        quit()
