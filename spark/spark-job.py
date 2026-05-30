"""
spark-job.py — Main Spark Structured Streaming Job
Reads transactions from Kafka → scores with ML model → writes to BigQuery
and publishes fraud alerts back to Kafka.
"""

import sys
import json
import logging
from datetime import datetime, timezone

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import from_json, col, current_timestamp, lit, udf
from pyspark.sql.types import (
    StructType, StringType, DoubleType, BooleanType, FloatType
)

# Add streaming app to path
sys.path.insert(0, "/opt/spark")

from spark_streaming_app.fraud_detector      import FraudDetector
from spark_streaming_app.bigquery_writer     import write_batch
from spark_streaming_app.kafka_alert_producer import publish_alert

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Spark Session ─────────────────────────────────────────────────────────────
spark = SparkSession.builder \
    .appName("FraudDetectionStreaming") \
    .config("spark.sql.streaming.schemaInference", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
log.info("Spark session started — version %s", spark.version)

# ── Transaction Schema ────────────────────────────────────────────────────────
SCHEMA = StructType() \
    .add("transaction_id", StringType(),  nullable=False) \
    .add("user_id",        StringType(),  nullable=True) \
    .add("amount",         DoubleType(),  nullable=False) \
    .add("merchant",       StringType(),  nullable=True) \
    .add("timestamp",      StringType(),  nullable=True)

# ── Instantiate detector (shared across UDF calls via closure) ────────────────
detector = FraudDetector()

# ── UDFs ──────────────────────────────────────────────────────────────────────
@udf(returnType=BooleanType())
def udf_is_fraud(amount, user_id, merchant):
    return detector.predict(
        float(amount or 0),
        str(user_id  or ""),
        str(merchant or ""),
    )

@udf(returnType=FloatType())
def udf_fraud_proba(amount, user_id, merchant):
    return float(detector.predict_proba(
        float(amount or 0),
        str(user_id  or ""),
        str(merchant or ""),
    ))

# ── Read from Kafka ───────────────────────────────────────────────────────────
raw_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "transactions") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .option("maxOffsetsPerTrigger", 500) \
    .load()

log.info("Kafka stream connected")

# ── Parse JSON ────────────────────────────────────────────────────────────────
transactions = raw_stream \
    .selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), SCHEMA).alias("data")) \
    .select("data.*") \
    .filter(col("transaction_id").isNotNull())

# ── Score with ML model ───────────────────────────────────────────────────────
scored = transactions \
    .withColumn("is_fraud",    udf_is_fraud(col("amount"), col("user_id"), col("merchant"))) \
    .withColumn("fraud_score", udf_fraud_proba(col("amount"), col("user_id"), col("merchant"))) \
    .withColumn("processed_at", current_timestamp())

# ── foreachBatch sink: write to BigQuery + publish alerts ─────────────────────
def process_batch(batch_df: DataFrame, batch_id: int):
    rows = [row.asDict() for row in batch_df.collect()]
    if not rows:
        return

    log.info("Batch %d — %d transactions", batch_id, len(rows))

    # Persist all rows to BigQuery
    write_batch(rows)

    # Publish fraud alerts
    frauds = [r for r in rows if r.get("is_fraud")]
    for txn in frauds:
        publish_alert(txn)
    if frauds:
        log.info("Batch %d — %d fraud(s) detected and alerted", batch_id, len(frauds))

# ── Start streaming query ─────────────────────────────────────────────────────
query = scored.writeStream \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", "/tmp/spark-checkpoints/main") \
    .trigger(processingTime="5 seconds") \
    .outputMode("append") \
    .start()

log.info("Streaming query started — awaiting termination")
query.awaitTermination()