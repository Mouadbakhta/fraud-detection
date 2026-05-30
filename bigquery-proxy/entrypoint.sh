#!/bin/sh
set -e

echo "Starting BigQuery emulator..."
echo "Project: $BIGQUERY_PROJECT_ID"
echo "Dataset: $BIGQUERY_DATASET"

if [ -f /etc/bigquery/init-schema.json ]; then
    exec bigquery-emulator \
        --project=$BIGQUERY_PROJECT_ID \
        --dataset=$BIGQUERY_DATASET \
        --port=$PORT \
        --log-level=info \
        --data-from-yaml=/etc/bigquery/init-schema.json
else
    exec bigquery-emulator \
        --project=$BIGQUERY_PROJECT_ID \
        --dataset=$BIGQUERY_DATASET \
        --port=$PORT \
        --log-level=info
fi