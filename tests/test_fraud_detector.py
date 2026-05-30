"""
tests/test_fraud_detector.py
Unit tests for the FraudDetector class (no Spark needed).
"""
import sys
import os
import pytest

# Make the spark_streaming_app importable without Spark
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from spark.spark_streaming_app.fraud_detector import FraudDetector


# ── FraudDetector (rule-based fallback) ──────────────────────────────────────

class TestFraudDetectorRuleBased:
    """Tests against the threshold-based fallback (no model file present)."""

    def setup_method(self):
        # Force rule-based mode by pointing to a non-existent model path
        self.detector = FraudDetector(model_path="/tmp/does_not_exist.pkl")

    def test_high_amount_is_fraud(self):
        assert self.detector.predict(6000.0) is True

    def test_low_amount_is_not_fraud(self):
        assert self.detector.predict(50.0) is False

    def test_boundary_exactly_5000(self):
        # 5000 is NOT > 5000, so not fraud
        assert self.detector.predict(5000.0) is False

    def test_boundary_above_5000(self):
        assert self.detector.predict(5000.01) is True

    def test_predict_proba_high_amount(self):
        score = self.detector.predict_proba(11000.0)
        assert score >= 0.90

    def test_predict_proba_low_amount(self):
        score = self.detector.predict_proba(10.0)
        assert score <= 0.10

    def test_predict_proba_range(self):
        for amount in [0, 100, 1000, 5000, 10000]:
            score = self.detector.predict_proba(float(amount))
            assert 0.0 <= score <= 1.0, f"Score out of range for amount={amount}"

    def test_predict_with_user_and_merchant(self):
        # Should not raise even with extra args in rule-based mode
        result = self.detector.predict(9000.0, user_id="USR-1", merchant="Amazon")
        assert result is True

    def test_zero_amount(self):
        assert self.detector.predict(0.0) is False

    def test_negative_amount(self):
        # Negative amounts should not crash
        result = self.detector.predict(-100.0)
        assert isinstance(result, bool)


# ── BigQuery writer (unit, no network) ──────────────────────────────────────

class TestBigQueryWriter:
    """Smoke tests for bigquery_writer (mocked HTTP)."""

    def test_write_empty_batch_does_not_raise(self):
        from spark.spark_streaming_app.bigquery_writer import write_batch
        # Should silently return for empty list
        write_batch([])   # must not raise

    def test_write_batch_handles_network_error(self, monkeypatch):
        import requests
        from spark.spark_streaming_app import bigquery_writer

        def mock_post(*args, **kwargs):
            raise requests.RequestException("connection refused")

        monkeypatch.setattr(requests, "post", mock_post)
        # Must not raise, just log
        write_batch([{
            "transaction_id": "TXN-001",
            "user_id": "USR-001",
            "amount": 100.0,
            "merchant": "Test",
            "timestamp": "2024-01-01T00:00:00Z",
        }])


# ── Producer helpers ─────────────────────────────────────────────────────────

class TestProducerHelpers:
    """Test synthetic transaction generation."""

    def setup_method(self):
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "producer",
            pathlib.Path(__file__).parent.parent / "producer" / "producer.py"
        )
        self.mod = importlib.util.module_from_spec(spec)
        # Patch kafka import so producer.py loads without a broker
        import unittest.mock as mock
        with mock.patch.dict("sys.modules", {
            "kafka": mock.MagicMock(),
            "kafka.errors": mock.MagicMock(),
        }):
            spec.loader.exec_module(self.mod)

    def test_synthetic_transaction_has_required_fields(self):
        tx = self.mod.synthetic_transaction()
        for field in ["transaction_id", "user_id", "amount", "merchant", "timestamp"]:
            assert field in tx, f"Missing field: {field}"

    def test_synthetic_transaction_amount_positive(self):
        for _ in range(20):
            tx = self.mod.synthetic_transaction()
            assert tx["amount"] > 0

    def test_synthetic_transaction_id_format(self):
        tx = self.mod.synthetic_transaction()
        assert tx["transaction_id"].startswith("TXN-")