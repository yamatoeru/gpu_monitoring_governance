#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/gpu-agent"
BIN_DIR="${BASE_DIR}/bin"
PKG_DIR="${BASE_DIR}/pkg"
CONF_DIR="${BASE_DIR}/conf"
LOG_DIR="/var/log/gpu-agent"
TELEGRAF_CONF_TARGET="/etc/telegraf/telegraf.d/gpu-agent.conf"
SYSTEMD_DIR="/etc/systemd/system"

mkdir -p "${BIN_DIR}" "${PKG_DIR}" "${CONF_DIR}" "${LOG_DIR}"

cp ../agent/gpu_agent/main.py "${BIN_DIR}/gpu-agent.py"
cp -r ../agent/gpu_agent "${PKG_DIR}/"
cp linux-telegraf-gpu-agent.conf "${TELEGRAF_CONF_TARGET}"
cp gpu-agent-validate.service "${SYSTEMD_DIR}/gpu-agent-validate.service"
cp gpu-agent-validate.timer "${SYSTEMD_DIR}/gpu-agent-validate.timer"
cp dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"

cat > "${BIN_DIR}/gpu-agent" <<'WRAP'
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=/opt/gpu-agent/pkg
exec python3 /opt/gpu-agent/bin/gpu-agent.py "$@"
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
systemctl enable gpu-agent-validate.timer
systemctl start gpu-agent-validate.timer

echo "Installed. Next steps:"
echo "  1) ensure telegraf package is installed"
echo "  2) place dcgm-exporter binary at /usr/local/bin/dcgm-exporter"
echo "  3) systemctl enable --now telegraf dcgm-exporter"
echo "  4) /opt/gpu-agent/bin/gpu-agent validate"
