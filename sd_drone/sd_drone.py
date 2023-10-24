import json
import socket

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

        # Enviar la información
        # TODO

def get_direction(a, b):
    d = b - a

    if d > 0:
        return 1
    if d < 0:
        return -1
    return 0

# Pruebas
if __name__ == "__main__":
    drone = Drone(0, "dron")
    print(str(drone))
    drone.step_toward(5, 5)
    print(str(drone))
