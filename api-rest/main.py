# main.py — API REST FastAPI
# Expose les résultats de détection de fraude

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app
import time
import os

app = FastAPI(title="Fraud Detection API", version="1.0.0")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# ── Métriques Prometheus ──────────────────────────────────────────────────────
transactions_processed_total = Counter(
    'transactions_processed_total',
    'Total transactions traitées'
)
frauds_detected_total = Counter(
    'frauds_detected_total',
    'Total fraudes détectées'
)
processing_latency_seconds = Histogram(
    'processing_latency_seconds',
    'Latence de traitement',
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0]
)

# Monter /metrics sur le port principal
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/transactions")
def get_transactions():
    # TODO: remplacer par une vraie requête BigQuery
    return {"transactions": [], "total": 0}

@app.get("/frauds")
def get_frauds():
    # TODO: remplacer par une vraie requête BigQuery
    return {"frauds": [], "total": 0}

@app.get("/stats")
def get_stats():
    # TODO: calculer depuis BigQuery
    return {
        "total_transactions": 0,
        "total_frauds": 0,
        "fraud_rate": 0.0,
        "avg_latency": 0.0
    }