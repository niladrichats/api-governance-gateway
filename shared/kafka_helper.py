import os
import json
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
import time

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def get_producer(retries=5, delay=3):
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            return producer
        except NoBrokersAvailable:
            print(f"Kafka not ready, retrying in {delay}s... (attempt {attempt + 1}/{retries})")
            time.sleep(delay)
    raise Exception("Could not connect to Kafka after multiple retries")


def get_consumer(topic: str, group_id: str, retries=5, delay=3):
    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True
            )
            return consumer
        except NoBrokersAvailable:
            print(f"Kafka not ready, retrying in {delay}s... (attempt {attempt + 1}/{retries})")
            time.sleep(delay)
    raise Exception("Could not connect to Kafka after multiple retries")


def publish_event(topic: str, event: dict):
    producer = get_producer()
    producer.send(topic, event)
    producer.flush()
    producer.close()
    print(f"Published event to {topic}: {event}")
