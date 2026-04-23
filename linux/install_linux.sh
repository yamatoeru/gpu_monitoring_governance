#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/gpu-agent"
BIN_DIR="${BASE_DIR}/bin"
PKG_DIR="${BASE_DIR}/pkg"
CONF_DIR="${BASE_DIR}/conf"
LOG_DIR="/var/log/gpu-agent"
TELEGRAF_CONF_TARGET="/etc/telegraf/telegraf.d/gpu-agent.conf"
SYSTEMD_DIR="/etc/systemd/system"
TELEGRAF_VERSION="${TELEGRAF_VERSION:-1.33.3}"
TELEGRAF_DEB_URL="${TELEGRAF_DEB_URL:-https://dl.influxdata.com/telegraf/releases/telegraf_${TELEGRAF_VERSION}-1_amd64.deb}"
TELEGRAF_TMP_DEB="/tmp/telegraf_${TELEGRAF_VERSION}_amd64.deb"

mkdir -p "${BIN_DIR}" "${PKG_DIR}" "${CONF_DIR}" "${LOG_DIR}"

if ! command -v telegraf >/dev/null 2>&1; then
  curl -fsSL "${TELEGRAF_DEB_URL}" -o "${TELEGRAF_TMP_DEB}"
  apt-get update -y
  apt-get install -y "${TELEGRAF_TMP_DEB}"
fi

mkdir -p "$(dirname "${TELEGRAF_CONF_TARGET}")"

cp -r ../agent/gpu_agent "${PKG_DIR}/"
cp linux-telegraf-gpu-agent.conf "${TELEGRAF_CONF_TARGET}"
cp gpu-agent-validate.service "${SYSTEMD_DIR}/gpu-agent-validate.service"
cp gpu-agent-validate.timer "${SYSTEMD_DIR}/gpu-agent-validate.timer"
cp dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"

cat > "${BIN_DIR}/gpu-agent" <<'WRAP'
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=/opt/gpu-agent/pkg
exec python3 -m gpu_agent.main "$@"
WRAP
chmod +x "${BIN_DIR}/gpu-agent"

mkdir -p /etc/default
cat > /etc/default/gpu-agent <<'ENV'
GPU_AGENT_ENV_TYPE=vm
GPU_AGENT_CONFIG_VERSION=2026.04.23
GPU_AGENT_LATEST_VERSION_URL=http://repo.internal/gpu-agent/latest_version.json
GPU_AGENT_DCGM_METRICS_URL=http://127.0.0.1:9400/metrics
# GPU_AGENT_INGEST_URL=http://ingest.internal:8080/events
# GPU_AGENT_INGEST_TOKEN=
ENV

systemctl daemon-reload
systemctl enable telegraf
systemctl restart telegraf
systemctl enable gpu-agent-validate.timer
systemctl start gpu-agent-validate.timer

echo "Installed. Next steps:"
echo "  1) place dcgm-exporter binary at /usr/local/bin/dcgm-exporter"
echo "  2) systemctl enable --now dcgm-exporter"
echo "  3) /opt/gpu-agent/bin/gpu-agent validate"
