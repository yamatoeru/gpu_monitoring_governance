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
TELEGRAF_FORCE_VERSION="${TELEGRAF_FORCE_VERSION:-false}"
MANAGE_DCGM_SERVICE="${GPU_AGENT_MANAGE_DCGM_SERVICE:-false}"

mkdir -p "${BIN_DIR}" "${PKG_DIR}" "${CONF_DIR}" "${LOG_DIR}"

current_telegraf_version() {
  if ! command -v telegraf >/dev/null 2>&1; then
    return 1
  fi
  telegraf --version 2>/dev/null | awk '{print $2; exit}'
}

install_telegraf() {
  curl -fsSL "${TELEGRAF_DEB_URL}" -o "${TELEGRAF_TMP_DEB}"
  apt-get update -y
  apt-get install -y "${TELEGRAF_TMP_DEB}"
}

TELEGRAF_ACTION="install"
if command -v telegraf >/dev/null 2>&1; then
  TELEGRAF_ACTION="preserve"
  CURRENT_TELEGRAF_VERSION="$(current_telegraf_version || true)"
  if [[ -n "${CURRENT_TELEGRAF_VERSION}" ]] && [[ "${CURRENT_TELEGRAF_VERSION}" != "${TELEGRAF_VERSION}" ]]; then
    echo "Detected existing telegraf version ${CURRENT_TELEGRAF_VERSION} (target ${TELEGRAF_VERSION})."
    if [[ "${TELEGRAF_FORCE_VERSION}" == "true" ]]; then
      echo "TELEGRAF_FORCE_VERSION=true, replacing installed Telegraf with ${TELEGRAF_VERSION}."
      TELEGRAF_ACTION="replace"
      install_telegraf
    else
      echo "Preserving existing Telegraf. Set TELEGRAF_FORCE_VERSION=true to replace it."
    fi
  fi
else
  install_telegraf
fi

mkdir -p "$(dirname "${TELEGRAF_CONF_TARGET}")"

cp -r ../agent/gpu_agent "${PKG_DIR}/"
cp linux-telegraf-gpu-agent.conf "${TELEGRAF_CONF_TARGET}"
cp gpu-agent-validate.service "${SYSTEMD_DIR}/gpu-agent-validate.service"
cp gpu-agent-validate.timer "${SYSTEMD_DIR}/gpu-agent-validate.timer"
if [[ ! -f "${SYSTEMD_DIR}/dcgm-exporter.service" ]]; then
  cp dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"
elif ! cmp -s dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"; then
  if [[ "${MANAGE_DCGM_SERVICE}" == "true" ]]; then
    cp "${SYSTEMD_DIR}/dcgm-exporter.service" "${SYSTEMD_DIR}/dcgm-exporter.service.gpu-agent.bak"
    cp dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"
    echo "Replaced existing dcgm-exporter.service and backed up the previous file."
  else
    echo "Existing dcgm-exporter.service differs from bundled unit; preserving it."
    echo "Set GPU_AGENT_MANAGE_DCGM_SERVICE=true to replace it."
  fi
fi

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
GPU_AGENT_LATEST_VERSION_URL=https://raw.githubusercontent.com/yamatoeru/gpu_monitoring_governance/main/examples/latest_version.json
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
if [[ "${TELEGRAF_ACTION}" == "preserve" ]]; then
  echo "  - preserved existing telegraf installation"
elif [[ "${TELEGRAF_ACTION}" == "replace" ]]; then
  echo "  - replaced telegraf with version ${TELEGRAF_VERSION}"
fi
echo "  1) place dcgm-exporter binary at /usr/local/bin/dcgm-exporter"
echo "  2) systemctl enable --now dcgm-exporter"
echo "  3) /opt/gpu-agent/bin/gpu-agent validate"
