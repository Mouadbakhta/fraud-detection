"""
kafka_alert_producer.py — Publishes fraud alerts back to Kafka topic.
"""
import json
import logging
import os

from kafka import KafkaProducer
from kafka.errors import KafkaError

log = logging.getLogger(__name__)

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
ALERT_TOPIC = os.getenv("KAFKA_ALERT_TOPIC", "fraud-alerts")

_producer = None


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks=1,
        )
    return _producer


def publish_alert(transaction: dict):
    """Send a fraud alert to the fraud-alerts Kafka topic."""
    try:
        producer = _get_producer()
        producer.send(
            ALERT_TOPIC,
            key=transaction.get("transaction_id"),
            value={
                "alert_type": "FRAUD_DETECTED",
                "transaction_id": transaction.get("transaction_id"),
                "user_id": transaction.get("user_id"),
                "amount": transaction.get("amount"),
                "merchant": transaction.get("merchant"),
                "timestamp": transaction.get("timestamp"),
                "processed_at": transaction.get("processed_at"),
            },
        )
    except KafkaError as exc:
        log.error(
            "Failed to publish alert for %s: %s",
            transaction.get("transaction_id"),
            exc,
        )
