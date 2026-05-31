#!/usr/bin/env python3
"""
Spark batch job — train a fraud detection model on historical data.
"""
import logging
import os
import pickle

import numpy as np
from pyspark.sql import SparkSession
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_OUTPUT_PATH = os.getenv("MODEL_PATH", "/app/models/fraud_model.pkl")


def generate_training_data(n=10000):
    """Generate synthetic training data."""
    np.random.seed(42)
    amounts = np.random.exponential(200, n)
    merchant_ids = np.random.randint(0, 1000, n)
    category_ids = np.random.randint(0, 10, n)
    country_ids = np.random.randint(0, 50, n)
    fraud_prob = (
        0.1 * (amounts > 2000).astype(float)
        + 0.2 * (country_ids > 30).astype(float)
        + 0.05 * (category_ids == 5).astype(float)
    )
    labels = (np.random.random(n) < fraud_prob).astype(int)
    X = np.column_stack([amounts, merchant_ids, category_ids, country_ids])
    return X, labels


def train_model():
    """Train and return a RandomForest fraud classifier."""
    logger.info("Generating training data...")
    X, y = generate_training_data(50000)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info("Training RandomForest model...")
    model = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    logger.info("\n" + classification_report(y_test, y_pred))
    return model


def save_model(model):
    """Persist model to disk."""
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    with open(MODEL_OUTPUT_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {MODEL_OUTPUT_PATH}")


def main():
    spark = SparkSession.builder.appName("FraudModelTraining").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    model = train_model()
    save_model(model)
    spark.stop()


if __name__ == "__main__":
    main()
