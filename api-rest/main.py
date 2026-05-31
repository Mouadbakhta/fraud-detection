import json
import logging
import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.api_core.client_options import ClientOptions
from google.cloud import bigquery
from kafka import KafkaProducer
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fraud Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
BIGQUERY_EMULATOR_HOST = os.getenv("BIGQUERY_EMULATOR_HOST", "bigquery:9050")
BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "fraud-detection-project")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "transactions")


def get_bq_client():
    options = ClientOptions(api_endpoint=f"http://{BIGQUERY_EMULATOR_HOST}")
    return bigquery.Client(
        project=BIGQUERY_PROJECT_ID,
        client_options=options,
    )


class Transaction(BaseModel):
    transaction_id: str
    amount: float
    merchant: str
    timestamp: Optional[str] = None
    user_id: Optional[str] = None


class FraudAlert(BaseModel):
    transaction_id: str
    fraud_score: float
    is_fraud: bool
    timestamp: str


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
def root():
    return {"message": "Fraud Detection API", "version": "1.0.0"}


@app.post("/transactions")
def submit_transaction(transaction: Transaction):
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        if not transaction.timestamp:
            transaction.timestamp = datetime.utcnow().isoformat()
        producer.send("transactions", value=transaction.dict())
        producer.flush()
        return {"status": "submitted", "transaction_id": transaction.transaction_id}
    except Exception as e:
        logger.error(f"Error submitting transaction: {e}")
        raise


@app.get("/alerts", response_model=List[FraudAlert])
def get_fraud_alerts(limit: int = 100):
    try:
        client = get_bq_client()
        query = f"""
            SELECT transaction_id, fraud_score, is_fraud, timestamp
            FROM `{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET}.fraud_alerts`
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        results = client.query(query).result()
        alerts = []
        for row in results:
            alerts.append(
                FraudAlert(
                    transaction_id=row.transaction_id,
                    fraud_score=row.fraud_score,
                    is_fraud=row.is_fraud,
                    timestamp=str(row.timestamp),
                )
            )
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return []


@app.get("/stats")
def get_stats():
    try:
        client = get_bq_client()
        query = f"""
            SELECT
                COUNT(*) as total_transactions,
                SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
                AVG(fraud_score) as avg_fraud_score
            FROM `{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET}.fraud_alerts`
        """
        results = list(client.query(query).result())
        if results:
            row = results[0]
            return {
                "total_transactions": row.total_transactions,
                "fraud_count": row.fraud_count,
                "fraud_rate": (
                    row.fraud_count / row.total_transactions
                    if row.total_transactions > 0
                    else 0
                ),
                "avg_fraud_score": row.avg_fraud_score,
            }
        return {
            "total_transactions": 0,
            "fraud_count": 0,
            "fraud_rate": 0,
            "avg_fraud_score": 0,
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "total_transactions": 0,
            "fraud_count": 0,
            "fraud_rate": 0,
            "avg_fraud_score": 0,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
    )
