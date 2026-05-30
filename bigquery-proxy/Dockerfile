FROM alpine:3.18

RUN apk add --no-cache ca-certificates tzdata curl

# Download pre-built binary instead of compiling from source
RUN curl --retry 5 --retry-delay 3 --connect-timeout 30 --max-time 300 -L \
    https://github.com/goccy/bigquery-emulator/releases/download/v0.4.3/bigquery-emulator-linux-amd64 \
    -o /usr/local/bin/bigquery-emulator && \
    chmod +x /usr/local/bin/bigquery-emulator

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]