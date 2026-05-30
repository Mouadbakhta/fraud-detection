FROM apache/spark:3.5.0
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-dev curl wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

ENV SPARK_VERSION=3.5.0 \
    SCALA_VERSION=2.12 \
    KAFKA_JAR_VERSION=0-10

RUN mkdir -p /opt/spark/jars && \
    wget -q "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}/${SPARK_VERSION}/spark-sql-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}-${SPARK_VERSION}.jar" \
        -O /opt/spark/jars/spark-sql-kafka.jar && \
    wget -q "https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.0/kafka-clients-3.5.0.jar" \
        -O /opt/spark/jars/kafka-clients.jar && \
    wget -q "https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}/${SPARK_VERSION}/spark-streaming-kafka-${KAFKA_JAR_VERSION}_${SCALA_VERSION}-${SPARK_VERSION}.jar" \
        -O /opt/spark/jars/spark-streaming-kafka.jar

ENV SPARK_HOME=/opt/spark \
    PYSPARK_PYTHON=python3 \
    SPARK_MASTER_URL=spark://spark-master:7077 \
    KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
    BIGQUERY_PROJECT_ID=fraud-detection-project \
    BIGQUERY_DATASET=transactions \
    MODEL_PATH=/app/models/fraud_model.pkl

WORKDIR /app
COPY spark_streaming_app/ /app/
COPY models/ /app/models/

RUN chmod -R 755 /app && chown -R 185:185 /app
USER 185

EXPOSE 4040 7077 8080