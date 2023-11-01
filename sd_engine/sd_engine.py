import json
import socket
import sys
from kafka import KafkaProducer
from kafka.struct import TopicPartition

class Engine:
    def __init__(engine_adress, broker_adress):
        self.engine_adress = engine_adress
        self.broker_adress = broker_adress

        # Productor de posiciones y direccionamiento
        self.producer = KafkaProducer(
            bootstrap_servers = [broker_adress],
            value_serializer = lambda msg: msg.encode("utf-8")
        )

        # Consumidor de desplazamiento
        self.consumer = KafkaConsumer(
            "drone_movement",
            broker_servers = [broker_adress],
            auto_offset_reset = "earliest",
            enable_auto_commit = True,
            # group_id = "engine",
            value_deserializer = lambda msg: msg.decode("utf-8")
        )

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise Exception("Not enough arguments")

    # Conexión con Kafka
    engine_adress = sys.argv[1]
    broker_adress = sys.argv[2]

    try:
        engine = new Engine()
    except Exception as e:
        print(str(e))
