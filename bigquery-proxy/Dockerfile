FROM golang:1.21-alpine AS builder

# Installer le BigQuery Emulator (pour dev/test local)
RUN go install github.com/goccy/bigquery-emulator/cmd/bigquery-emulator@v0.4.3

# Image finale légère
FROM alpine:3.18

RUN apk add --no-cache ca-certificates tzdata

COPY --from=builder /go/bin/bigquery-emulator /usr/local/bin/bigquery-emulator

# Configuration
ENV BIGQUERY_PROJECT_ID=fraud-detection-project \
    BIGQUERY_DATASET=transactions \
    PORT=9050

# Script d'initialisation du schéma
COPY init-schema.json /etc/bigquery/init-schema.json
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9050

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:9050/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
