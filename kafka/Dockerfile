FROM confluentinc/cp-kafka:7.5.0

# Variables d'environnement par défaut (surchargées par docker-compose)
ENV KAFKA_BROKER_ID=1 \
    KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
    KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092 \
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
    KAFKA_AUTO_CREATE_TOPICS_ENABLE=true \
    KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,PLAINTEXT_HOST://0.0.0.0:29092 \
    KAFKA_LOG_RETENTION_HOURS=24 \
    KAFKA_LOG_SEGMENT_BYTES=1073741824 \
    KAFKA_NUM_PARTITIONS=3 \
    # Activer JMX pour Prometheus
    KAFKA_JMX_PORT=9999 \
    KAFKA_JMX_HOSTNAME=kafka 
    # Télécharger le JMX Exporter pour Prometheus
USER root
RUN mkdir -p /opt/jmx_exporter && \
    curl -L https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.19.0/jmx_prometheus_javaagent-0.19.0.jar \
    -o /opt/jmx_exporter/jmx_prometheus_javaagent.jar

# Copier la configuration JMX
COPY kafka-jmx-config.yml /opt/jmx_exporter/kafka-config.yml

# Script d'initialisation des topics
COPY init-topics.sh /usr/local/bin/init-topics.sh
RUN chmod +x /usr/local/bin/init-topics.sh

USER appuser

EXPOSE 9092 9999 7075

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD kafka-topics --bootstrap-server localhost:9092 --list || exit 1
