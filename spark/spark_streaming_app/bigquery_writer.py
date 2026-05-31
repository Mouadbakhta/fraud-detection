"""
bigquery_writer.py — BigQuery Sink for Spark Structured Streaming
Writes fraud-scored transactions to the BigQuery emulator.
"""
import logging
import os

import requests
from datetime import datetime, timezone

log = logging.getLogger(__name__)

BQ_HOST = os.getenv("BIGQUERY_EMULATOR_HOST", "bigquery:9050")
PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "fraud-detection-project")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "transactions")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "raw_transactions")

BASE_URL = f"http://{BQ_HOST}/bigquery/v2/projects/{PROJECT_ID}"


def _insert_rows(rows: list[dict]) -> bool:
    """
    Insert rows into BigQuery emulator via the REST insertAll endpoint.
    Falls back gracefully if the emulator is unreachable.
    """
    url = f"{BASE_URL}/datasets/{DATASET_ID}/tables/{TABLE_ID}/insertAll"
    payload = {
        "rows": [{"insertId": r.get("transaction_id", ""), "json": r} for r in rows]
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            return True
        log.error("BigQuery insert failed [%d]: %s", resp.status_code, resp.text[:200])
        return False
    except requests.RequestException as exc:
        log.error("BigQuery unreachable: %s", exc)
        return False


def write_batch(transactions: list[dict]):
    """Called from the Spark foreachBatch sink."""
    if not transactions:
        return
    now = datetime.now(timezone.utc).isoformat()
    enriched = [{**t, "processed_at": now} for t in transactions]
    ok = _insert_rows(enriched)
    log.info("Wrote %d rows to BigQuery — success=%s", len(enriched), ok)
