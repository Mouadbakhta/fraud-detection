FROM bitnami/spark:3.4.1

# Passer en root pour les installations
USER root

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python pour le ML et le streaming
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Télécharger les JARs nécessaires pour Kafka + BigQuery
ENV SPARK_VERSION=3.4.1 \
    SCALA_VERSION=2.12 \
    KAFKA_JAR_VERSION=0-10

RUN mkdir -p /opt/spark/jars && \
    # Connecteur Kafka pour Spark Streaming
    wget -q "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}/${SPARK_VERSION}/spark-sql-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}-${SPARK_VERSION}.jar" \
    -O /opt/spark/jars/spark-sql-kafka.jar && \
    # Token provider Kafka
    wget -q "https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar" \
    -O /opt/spark/jars/kafka-clients.jar && \
    # Spark streaming Kafka
    wget -q "https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}/${SPARK_VERSION}/spark-streaming-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}-${SPARK_VERSION}.jar" \
    -O /opt/spark/jars/spark-streaming-kafka.jar

# Variables d'environnement Spark
ENV SPARK_HOME=/opt/bitnami/spark \
    PYSPARK_PYTHON=python3 \
    SPARK_MASTER_URL=spark://spark-master:7077 \
    KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
    BIGQUERY_PROJECT_ID=fraud-detection-project \
    BIGQUERY_DATASET=transactions \
    MODEL_PATH=/app/models/fraud_model.pkl

# Copier l'application Spark Streaming
WORKDIR /app
COPY spark_streaming_app/ /app/
COPY models/ /app/models/

# Permissions
RUN chmod -R 755 /app && chown -R 1001:1001 /app

USER 1001

EXPOSE 4040 7077 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:4040 || exit 1

# Lancer l'application de détection de fraude
CMD ["spark-submit", \
     "--master", "spark://spark-master:7077", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1", \
     "--conf", "spark.streaming.stopGracefullyOnShutdown=true", \
     "--conf", "spark.sql.streaming.checkpointLocation=/tmp/spark-checkpoints", \
     "/app/fraud_detection_streaming.py"]
