#!/usr/bin/env python3
"""
Kafka Producer — reads transactions from CSV and publishes to Kafka topic.
"""
import json
import logging
import os
import time

import pandas as pd
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
DATASET_PATH = os.getenv("DATASET_PATH", "/data/transactions.csv")
PUBLISH_RATE_MS = int(os.getenv("PUBLISH_RATE_MS", "100"))


def wait_for_kafka(retries=10, delay=5):
    for attempt in range(retries):
        try:
            producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
            producer.close()
            logger.info("Kafka is ready.")
            return True
        except NoBrokersAvailable:
            logger.warning(
                f"Kafka not ready, attempt {attempt + 1}/{retries},"
                f" retrying in {delay}s..."
            )
            time.sleep(delay)
    return False


def generate_synthetic_transaction(i):
    """Generate a synthetic transaction if no CSV is available."""
    import random

    merchants = [
        "Amazon", "Walmart", "Target", "BestBuy",
        "Apple", "Netflix", "Uber", "Airbnb",
    ]
    return {
        "transaction_id": f"TXN{i:08d}",
        "amount": round(random.uniform(1.0, 5000.0), 2),
        "merchant": random.choice(merchants),
        "user_id": f"USER{random.randint(1, 1000):04d}",
        "timestamp": pd.Timestamp.now().isoformat(),
        "category": random.choice(
            ["retail", "food", "travel", "entertainment", "utilities"]
        ),
        "country": random.choice(["US", "FR", "GB", "DE", "JP"]),
    }


def main():
    if not wait_for_kafka():
        logger.error("Could not connect to Kafka. Exiting.")
        return

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=3,
    )

    sleep_time = PUBLISH_RATE_MS / 1000.0

    if os.path.exists(DATASET_PATH):
        logger.info(f"Loading dataset from {DATASET_PATH}")
        df = pd.read_csv(DATASET_PATH)
        logger.info(
            f"Loaded {len(df)} transactions. Publishing to topic '{KAFKA_TOPIC}'..."
        )
        i = 0
        while True:
            row = df.iloc[i % len(df)].to_dict()
            row["timestamp"] = pd.Timestamp.now().isoformat()
            producer.send(KAFKA_TOPIC, value=row)
            if i % 100 == 0:
                logger.info(f"Published {i} transactions...")
                producer.flush()
            i += 1
            time.sleep(sleep_time)
    else:
        logger.warning(
            f"No dataset at {DATASET_PATH}, generating synthetic transactions."
        )
        i = 0
        while True:
            transaction = generate_synthetic_transaction(i)
            producer.send(KAFKA_TOPIC, value=transaction)
            if i % 100 == 0:
                logger.info(f"Published {i} synthetic transactions...")
                producer.flush()
            i += 1
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()




    