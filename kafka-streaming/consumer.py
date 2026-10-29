"""Classify records; acknowledge each input only after confirmed Kafka output."""
import json
import math
import os
import time

import requests
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.errors import NoBrokersAvailable
from kafka.structs import OffsetAndMetadata

BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
IN_TOPIC = os.environ.get("MESSAGES_TOPIC", "messages")
OUT_TOPIC = os.environ.get("PREDICTIONS_TOPIC", "predictions")
API = os.environ.get("MODEL_API", "http://spam-api:8000/predict")


def connect_consumer():
    while True:
        try:
            return KafkaConsumer(IN_TOPIC, bootstrap_servers=BROKER,
                auto_offset_reset="earliest", group_id="spam-inference",
                enable_auto_commit=False, max_poll_records=1,
                max_poll_interval_ms=120_000,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")))
        except NoBrokersAvailable:
            print("consumer: waiting for kafka...", flush=True)
            time.sleep(3)


def predict(text, attempts=3):
    """Retry temporary transport/429/5xx failures, not permanent bad requests."""
    for attempt in range(attempts):
        try:
            response = requests.post(API, json={"text": text}, timeout=10)
            response.raise_for_status()
            result = response.json()
            confidence = result["confidence"]
            if result["label"] not in {"ham", "spam"} or isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError("Invalid prediction response")
            return result
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as error:
            status = error.response.status_code if error.response is not None else None
            if status is not None and status != 429 and status < 500:
                raise
            if attempt + 1 == attempts:
                raise
            time.sleep(1)
    raise ValueError("attempts must be positive")


def process_record(record, consumer, producer):
    message = record.value
    if not isinstance(message, dict) or not isinstance(message.get("text"), str):
        raise ValueError("Kafka input must be an object with string text")
    result = predict(message["text"])
    event_id = f"{record.topic}:{record.partition}:{record.offset}"
    output = {"id": message.get("id"), "event_id": event_id, "text": message["text"], **result}
    producer.send(OUT_TOPIC, output, key=event_id.encode()).get(timeout=30)
    partition = TopicPartition(record.topic, record.partition)
    consumer.commit({partition: OffsetAndMetadata(record.offset + 1, "", -1)})
    print(json.dumps(output), flush=True)
    return output


def main():
    consumer = connect_consumer()
    producer = None
    try:
        producer = KafkaProducer(bootstrap_servers=BROKER, acks="all", retries=5,
            max_in_flight_requests_per_connection=1,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"))
        for record in consumer:
            process_record(record, consumer, producer)
    finally:
        consumer.close(autocommit=False)
        if producer is not None:
            producer.close(timeout=10)


if __name__ == "__main__":
    main()
