FROM python:3.11-slim

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root
RUN useradd -m -u 1000 apiuser

WORKDIR /app

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'API
COPY . .

# Permissions
RUN chown -R apiuser:apiuser /app

USER apiuser

# Variables d'environnement
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
    BIGQUERY_PROJECT_ID=fraud-detection-project \
    BIGQUERY_DATASET=transactions \
    BIGQUERY_EMULATOR_HOST=bigquery:9050 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    LOG_LEVEL=info

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--log-level", "info", "--workers", "2"]
