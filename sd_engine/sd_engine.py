import json
import socket
import sys
from kafka import KafkaProducer

class Engine:
    def __init__(self):
        pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise Exception("Not enough arguments")

    # Conexión con Kafka
    kafka_host = sys.argv[1]
    kafka_port = sys.argv[2]

    try:
        producer = KafkaProducer(
            bootstrap_servers = [f"{kafka_host}:{kafka_port}"],
            value_serializer = lambda msg: msg.encode("utf-8")
        )
        producer.send("engine-topic", value="Hello world!")
    except:
        print(f"Error connectiong to {kafka_host}:{kafka_port}")
