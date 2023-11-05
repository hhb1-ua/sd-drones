import sys
import threading
import kafka
import time

BROKER_ADRESS = "kafka:9092"
REQUEST_TIMEOUT = 10

def consume(topic, partition):
    consumer = kafka.KafkaConsumer(
        bootstrap_servers = [BROKER_ADRESS],
        value_deserializer = lambda msg: msg.decode("utf-8"),
        consumer_timeout_ms = REQUEST_TIMEOUT * 1000
    )

    consumer.assign([kafka.TopicPartition(topic, partition)])

    for message in consumer:
        print(message.value)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <topic> <partition>")
        quit()

    print("<START>")
    consume(sys.argv[1], int(sys.argv[2]))
    print("<END>")
