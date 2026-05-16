FROM grafana/grafana:10.1.2

# Passer en root pour les installations
USER root

# Installer les plugins Grafana utiles
RUN grafana-cli plugins install grafana-piechart-panel && \
    grafana-cli plugins install grafana-worldmap-panel && \
    grafana-cli plugins install vonage-status-panel

# Variables d'environnement
ENV GF_SECURITY_ADMIN_USER=admin \
    GF_SECURITY_ADMIN_PASSWORD=fraud2024! \
    GF_USERS_ALLOW_SIGN_UP=false \
    GF_SERVER_DOMAIN=localhost \
    GF_SERVER_HTTP_PORT=3000 \
    GF_ANALYTICS_REPORTING_ENABLED=false \
    # Provisioning automatique
    GF_PATHS_PROVISIONING=/etc/grafana/provisioning \
    GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/var/lib/grafana/dashboards/fraud-overview.json

# Copier les configurations de provisioning
COPY provisioning/ /etc/grafana/provisioning/
COPY dashboards/ /var/lib/grafana/dashboards/

# Ajuster les permissions
RUN chown -R grafana:grafana /etc/grafana/provisioning /var/lib/grafana/dashboards

USER grafana

EXPOSE 3000

VOLUME ["/var/lib/grafana"]

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
    CMD wget -qO- http://admin:fraud2024!@localhost:3000/api/health || exit 1
