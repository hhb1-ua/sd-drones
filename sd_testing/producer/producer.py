import sys
import time
import kafka
import json

BROKER_ADRESS = "kafka:9092"

def get_partition_number(topic):
    consumer = kafka.KafkaConsumer(
        bootstrap_servers = [BROKER_ADRESS]
    )
    return len(consumer.partitions_for_topic(topic))

def send(topic, message, number, partition):
    # Crear particiones si es necesario
    if get_partition_number(topic) < partition + 1:
        admin = kafka.KafkaAdminClient(
            bootstrap_servers = [BROKER_ADRESS]
        )
        admin.create_partitions({topic: kafka.admin.new_partitions.NewPartitions(partition + 1)})

    producer = kafka.KafkaProducer(
        bootstrap_servers = [BROKER_ADRESS],
        value_serializer = lambda message: message.encode("utf-8")
    )

    for i in range(number):
        producer.send(topic, value = message, partition = partition)
        print(f"Successfully published <{message}> at <{topic}:{partition}>")
        time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <topic> <message> <number> <partition>")
        quit()

    topic = sys.argv[1]
    message = sys.argv[2]
    number = int(sys.argv[3])
    partition = int(sys.argv[4])

    try:
        send(topic, message, number, partition)
    except Exception as e:
        print(str(e))
        quit()
