import json
import socket
import sys

ENGINE_ADRESS = ("engine", 9010)
REGISTRY_ADRESS =  ("registry", 9020)
BROKER_ADRESS =  ("kafka", 9092)

class Drone:
    def __init__(self, identifier, alias):
        self.identifier = identifier
        self.alias = alias
        self.token = None
        self.x = 0
        self.y = 0

    def __str__(self):
        return json.dumps({
            "identifier": self.identifier,
            "alias": self.alias,
            "token": self.token,
            "position": {
                "x": self.x,
                "y": self.y
            }
        })

    def step_toward(self, dx, dy):
        # Comprobar que la posición está dentro del mapa
        if dx < 0 or dy < 0 or dx >= 20 or dy >= 20:
            raise Exception("Can't move out of bounds")

        # Mover el dron
        self.x += get_direction(self.x, dx)
        self.y += get_direction(self.y, dy)

    def identity_register(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((REGISTRY_ADRESS[0], REGISTRY_ADRESS[1]))

            message = json.dumps({
                "operation": "register",
                "identifier": self.identifier,
                "alias": self.alias
            })
            server.send(message.encode("utf-8"))

            response = server.recv(1024).decode("utf-8")
            response = json.loads(response)

            server.close()

            if response["accepted"]:
                self.token = response["token"]
                return True

        except Exception as e:
            server.close()
            raise e

        return False

    def identity_modify(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((REGISTRY_ADRESS[0], REGISTRY_ADRESS[1]))

            message = json.dumps({
                "operation": "modify",
                "identifier": self.identifier,
                "alias": self.alias
            })
            server.send(message.encode("utf-8"))

            response = server.recv(1024).decode("utf-8")
            response = json.loads(response)

            server.close()

            return response["accepted"]

        except Exception as e:
            server.close()
            raise e

        return False

    def identity_delete(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((REGISTRY_ADRESS[0], REGISTRY_ADRESS[1]))

            message = json.dumps({
                "operation": "delete",
                "identifier": self.identifier
            })
            server.send(message.encode("utf-8"))

            response = server.recv(1024).decode("utf-8")
            response = json.loads(response)

            server.close()

            return response["accepted"]

        except Exception as e:
            server.close()
            raise e

        return False

def get_direction(a, b):
    d = b - a

    if d > 0:
        return 1
    if d < 0:
        return -1
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <identifier> <alias> [<engine> <registry> <broker>]")
        quit()

    drone = Drone(int(sys.argv[1]), str(sys.argv[2]))
    print(drone)
