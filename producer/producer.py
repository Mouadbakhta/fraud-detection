"""
producer.py — Kafka Transaction Producer
Reads transactions from CSV and publishes them to Kafka topic.
"""

import os
import json
import time
import random
import logging
from datetime import datetime, timezone

import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError

# ── Config ────────────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC             = os.getenv("KAFKA_TOPIC", "transactions")
DATASET_PATH            = os.getenv("DATASET_PATH", "/data/transactions.csv")
PUBLISH_RATE_MS         = int(os.getenv("PUBLISH_RATE_MS", "100"))   # ms between messages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Helper: connect with retry ────────────────────────────────────────────────
def create_producer(retries: int = 10, delay: int = 5) -> KafkaProducer:
    for attempt in range(1, retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_block_ms=30_000,
            )
            log.info("Connected to Kafka at %s", KAFKA_BOOTSTRAP_SERVERS)
            return producer
        except KafkaError as exc:
            log.warning("Kafka not ready (attempt %d/%d): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Cannot connect to Kafka after %d attempts" % retries)


# ── Helper: generate synthetic transaction if no CSV ─────────────────────────
def synthetic_transaction() -> dict:
    merchants = ["Amazon", "Carrefour", "Total", "FNAC", "Zara", "Apple Store", "Casino"]
    return {
        "transaction_id": f"TXN-{random.randint(100000, 999999)}",
        "user_id":        f"USR-{random.randint(1000, 9999)}",
        "amount":         round(random.uniform(1.0, 12000.0), 2),
        "merchant":       random.choice(merchants),
        "timestamp":      datetime.now(timezone.utc).isoformat(),
    }


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    producer = create_producer()
    sleep_s  = PUBLISH_RATE_MS / 1000.0
    sent     = 0

    # ── Load CSV if available ─────────────────────────────────────────────────
    df = None
    if os.path.exists(DATASET_PATH):
        log.info("Loading dataset from %s", DATASET_PATH)
        df = pd.read_csv(DATASET_PATH)
        # Normalise column names to lowercase
        df.columns = [c.lower().strip() for c in df.columns]
        log.info("Dataset loaded: %d rows", len(df))
    else:
        log.warning("Dataset not found at %s — using synthetic data", DATASET_PATH)

    log.info("Publishing to topic '%s' every %d ms", KAFKA_TOPIC, PUBLISH_RATE_MS)

    idx = 0
    while True:
        try:
            if df is not None:
                row  = df.iloc[idx % len(df)].to_dict()
                # Ensure required fields exist
                msg = {
                    "transaction_id": str(row.get("transaction_id", f"TXN-{idx}")),
                    "user_id":        str(row.get("user_id", f"USR-{idx}")),
                    "amount":         float(row.get("amount", 0.0)),
                    "merchant":       str(row.get("merchant", "Unknown")),
                    "timestamp":      str(row.get("timestamp",
                                        datetime.now(timezone.utc).isoformat())),
                }
                idx += 1
            else:
                msg = synthetic_transaction()

            future = producer.send(
                KAFKA_TOPIC,
                key=msg["transaction_id"],
                value=msg,
            )
            future.get(timeout=10)   # wait for ack
            sent += 1

            if sent % 100 == 0:
                log.info("Published %d transactions", sent)

            time.sleep(sleep_s)

        except KafkaError as exc:
            log.error("Kafka send error: %s", exc)
            time.sleep(5)

        except KeyboardInterrupt:
            log.info("Stopping producer. Total sent: %d", sent)
            break

    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()