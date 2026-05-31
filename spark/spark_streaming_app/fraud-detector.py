"""
fraud_detector.py — Fraud Detection Logic
Wraps the ML model (or rule-based fallback) used by the Spark streaming job.
"""
import logging
import os

import joblib

log = logging.getLogger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "/opt/spark/models/fraud_model.pkl")


class FraudDetector:
    """
    Loads a scikit-learn model if available, otherwise falls back to
    simple rule-based detection so the pipeline keeps running.
    """

    def __init__(self, model_path: str = MODEL_PATH):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                log.info("Model loaded from %s", self.model_path)
            except Exception as exc:
                log.warning(
                    "Could not load model (%s) — using rule-based fallback", exc
                )
        else:
            log.warning(
                "Model not found at %s — using rule-based fallback", self.model_path
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def predict(self, amount: float, user_id: str = "", merchant: str = "") -> bool:
        """Return True if the transaction is likely fraudulent."""
        if self.model is not None:
            features = self._build_features(amount, user_id, merchant)
            return bool(self.model.predict([features])[0])
        return self._rule_based(amount)

    def predict_proba(
        self, amount: float, user_id: str = "", merchant: str = ""
    ) -> float:
        """Return fraud probability [0, 1]."""
        if self.model is not None:
            features = self._build_features(amount, user_id, merchant)
            proba = self.model.predict_proba([features])
            return float(proba[0][1])
        # Rule-based probability
        if amount > 10_000:
            return 0.95
        if amount > 5_000:
            return 0.70
        if amount > 2_000:
            return 0.30
        return 0.05

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_features(amount: float, user_id: str, merchant: str) -> list:
        """
        Feature vector for the ML model.
        Adjust to match whatever features your trained model expects.
        """
        return [
            float(amount),
            hash(user_id) % 10_000,   # numeric proxy for user
            hash(merchant) % 1_000,   # numeric proxy for merchant
        ]

    @staticmethod
    def _rule_based(amount: float) -> bool:
        """Simple threshold rule — replace once the real model is ready."""
        return amount > 5_000