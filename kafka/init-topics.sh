#!/bin/bash
# init-topics.sh — creates Kafka topics on first startup
# Called automatically by the Kafka container entrypoint

set -e

KAFKA_BIN="/opt/kafka/bin"
BOOTSTRAP="localhost:9092"

echo "Waiting for Kafka to be ready..."
# Wait until Kafka is accepting connections
until $KAFKA_BIN/kafka-topics.sh --bootstrap-server $BOOTSTRAP --list > /dev/null 2>&1; do
  sleep 2
done

echo "Kafka is up — creating topics..."

# ── Topic: raw transactions (input from producers) ──────────────────────────
$KAFKA_BIN/kafka-topics.sh --bootstrap-server $BOOTSTRAP \
  --create --if-not-exists \
  --topic transactions \
  --partitions 3 \
  --replication-factor 1

# ── Topic: fraud alerts (output from Spark ML model) ────────────────────────
$KAFKA_BIN/kafka-topics.sh --bootstrap-server $BOOTSTRAP \
  --create --if-not-exists \
  --topic fraud-alerts \
  --partitions 3 \
  --replication-factor 1

# ── Topic: processed results (for BigQuery sink) ────────────────────────────
$KAFKA_BIN/kafka-topics.sh --bootstrap-server $BOOTSTRAP \
  --create --if-not-exists \
  --topic processed-transactions \
  --partitions 3 \
  --replication-factor 1

echo "All topics created successfully:"
$KAFKA_BIN/kafka-topics.sh --bootstrap-server $BOOTSTRAP --list