FROM prom/prometheus:v2.47.0

# Passer en root pour copier les fichiers
USER root

# Créer les répertoires nécessaires
RUN mkdir -p /etc/prometheus /prometheus/data && \
    chown -R nobody:nobody /prometheus

# Copier la configuration Prometheus
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY alert-rules.yml /etc/prometheus/alert-rules.yml

# Valider la configuration au build
RUN promtool check config /etc/prometheus/prometheus.yml

USER nobody

EXPOSE 9090

VOLUME ["/prometheus/data"]

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:9090/-/healthy || exit 1

CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus/data", \
     "--storage.tsdb.retention.time=15d", \
     "--web.enable-lifecycle", \
     "--web.enable-admin-api", \
     "--log.level=info"]
