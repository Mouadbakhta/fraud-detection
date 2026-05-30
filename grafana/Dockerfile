FROM grafana/grafana:10.1.2

# 1. Switch to root to install plugins
USER root

# 2. Install useful Grafana plugins
RUN grafana-cli plugins install grafana-piechart-panel && \
    grafana-cli plugins install grafana-worldmap-panel && \
    grafana-cli plugins install vonage-status-panel

# 3. Environment Variables
ENV GF_SECURITY_ADMIN_USER=admin \
    GF_SECURITY_ADMIN_PASSWORD=fraud2024! \
    GF_USERS_ALLOW_SIGN_UP=false \
    GF_SERVER_DOMAIN=localhost \
    GF_SERVER_HTTP_PORT=3000 \
    GF_ANALYTICS_REPORTING_ENABLED=false \
    GF_PATHS_PROVISIONING=/etc/grafana/provisioning \
    GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/var/lib/grafana/dashboards/fraud-overview.json

# 4. Copy configurations AND set permissions simultaneously
# Using 472:472 (Grafana's default UID/GID) avoids the "unknown user" build error
COPY --chown=472:472 provisioning/ /etc/grafana/provisioning/
COPY --chown=472:472 dashboards/ /var/lib/grafana/dashboards/

# 5. Remove the manual 'RUN chown' line as it is now redundant and causing errors

# 6. Switch back to the Grafana user (using ID 472 for compatibility)
USER 472

EXPOSE 3000

VOLUME ["/var/lib/grafana"]

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
    CMD wget -qO- http://admin:fraud2024!@localhost:3000/api/health || exit 1