#!/usr/bin/env bash
set -euo pipefail

# ======= CONFIG =======
NETWORK="parking-network"

EXPORTER_IMAGE="monitoring-metrics-exporter"
EXPORTER_CONTAINER="metrics-exporter"
EXPORTER_PORT_HOST=9090
EXPORTER_PORT_CONT=9090

PROM_IMAGE="prom/prometheus:v2.47.0"
PROM_CONTAINER="prometheus"
PROM_PORT_HOST=9091
PROM_PORT_CONT=9090
PROM_CONFIG_HOST_PATH="$PWD/prometheus/prometheus.yml"
PROM_CONFIG_CONT_PATH="/etc/prometheus/prometheus.yml"

GRAF_IMAGE="grafana/grafana:10.1.0"
GRAF_CONTAINER="grafana"
GRAF_PORT_HOST=3000
GRAF_PORT_CONT=3000
GRAF_ADMIN_USER="admin"
GRAF_ADMIN_PASS="admin123"
GRAF_PROVISIONING_HOST_PATH="$PWD/grafana/provisioning"
GRAF_PROVISIONING_CONT_PATH="/etc/grafana/provisioning"

# App URL (PROMIJENI AKO TREBA)
APP_URL="${APP_URL:-http://parking-app:5000}"
# APP_URL="${APP_URL:-http://host.docker.internal:5000}"
METRICS_PORT="${METRICS_PORT:-9090}"
SCRAPE_INTERVAL="${SCRAPE_INTERVAL:-15}"

# ======= HELPERS =======
say() { echo -e "\n==> $*\n"; }

ensure_file() {
  local p="$1"
  if [[ ! -f "$p" ]]; then
    echo "ERROR: File not found: $p" >&2
    exit 1
  fi
}

ensure_dir() {
  local p="$1"
  if [[ ! -d "$p" ]]; then
    echo "ERROR: Directory not found: $p" >&2
    exit 1
  fi
}

rm_container_if_exists() {
  local name="$1"
  docker rm -f "$name" >/dev/null 2>&1 || true
}

# ======= VALIDATION =======
ensure_file "$PROM_CONFIG_HOST_PATH"
ensure_dir "$GRAF_PROVISIONING_HOST_PATH"

# ======= NETWORK =======
say "Ensuring network: $NETWORK"
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null

# ======= EXPORTER =======
say "Building exporter image: $EXPORTER_IMAGE"
docker build -t "$EXPORTER_IMAGE" -f Dockerfile.metrics .

say "Starting exporter container: $EXPORTER_CONTAINER (APP_URL=$APP_URL)"
rm_container_if_exists "$EXPORTER_CONTAINER"
docker run -d \
  --name "$EXPORTER_CONTAINER" \
  --network "$NETWORK" \
  --add-host=host.docker.internal:host-gateway \
  --restart unless-stopped \
  -p "$EXPORTER_PORT_HOST:$EXPORTER_PORT_CONT" \
  -e "APP_URL=$APP_URL" \
  -e "METRICS_PORT=$METRICS_PORT" \
  -e "SCRAPE_INTERVAL=$SCRAPE_INTERVAL" \
  "$EXPORTER_IMAGE" >/dev/null

# ======= PROMETHEUS =======
say "Starting Prometheus: $PROM_CONTAINER"
rm_container_if_exists "$PROM_CONTAINER"
docker run -d \
  --name "$PROM_CONTAINER" \
  --network "$NETWORK" \
  --restart unless-stopped \
  -p "$PROM_PORT_HOST:$PROM_PORT_CONT" \
  -v "$PROM_CONFIG_HOST_PATH:$PROM_CONFIG_CONT_PATH:ro" \
  "$PROM_IMAGE" \
  --config.file="$PROM_CONFIG_CONT_PATH" >/dev/null

# ======= GRAFANA =======
say "Starting Grafana: $GRAF_CONTAINER"
rm_container_if_exists "$GRAF_CONTAINER"
docker volume create grafana-data >/dev/null 2>&1 || true
docker run -d \
  --name "$GRAF_CONTAINER" \
  --network "$NETWORK" \
  --restart unless-stopped \
  -p "$GRAF_PORT_HOST:$GRAF_PORT_CONT" \
  -e "GF_SECURITY_ADMIN_USER=$GRAF_ADMIN_USER" \
  -e "GF_SECURITY_ADMIN_PASSWORD=$GRAF_ADMIN_PASS" \
  -v grafana-data:/var/lib/grafana \
  -v "$GRAF_PROVISIONING_HOST_PATH:$GRAF_PROVISIONING_CONT_PATH:ro" \
  "$GRAF_IMAGE" >/dev/null

# ======= QUICK CHECKS =======
say "Quick checks (may take a few seconds on first run)..."
sleep 2

echo "Exporter metrics:   http://localhost:${EXPORTER_PORT_HOST}/metrics"
echo "Prometheus UI:      http://localhost:${PROM_PORT_HOST}"
echo "Grafana UI:         http://localhost:${GRAF_PORT_HOST} (login: $GRAF_ADMIN_USER / $GRAF_ADMIN_PASS)"

# Optional: basic curl checks (ignore if curl not installed)
if command -v curl >/dev/null 2>&1; then
  echo
  echo "Exporter parking_app_up (if reachable):"
  curl -s "http://localhost:${EXPORTER_PORT_HOST}/metrics" | grep -E "parking_app_up" || true
  echo
  echo "Prometheus targets page (HTTP code):"
  curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:${PROM_PORT_HOST}/targets" || true
fi

say "Done."
