#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/gpu-agent"
BIN_DIR="${BASE_DIR}/bin"
PKG_DIR="${BASE_DIR}/pkg"
CONF_DIR="${BASE_DIR}/conf"
LOG_DIR="/var/log/gpu-agent"
AGENT_LINK_TARGET="/usr/local/bin/gpu-agent"
TELEGRAF_CONF_TARGET="/etc/telegraf/telegraf.d/gpu-agent.conf"
SYSTEMD_DIR="/etc/systemd/system"
DCGM_EXPORTER_TARGET="/usr/local/bin/dcgm-exporter"
TELEGRAF_VERSION="${TELEGRAF_VERSION:-1.33.3}"
TELEGRAF_DEB_URL="${TELEGRAF_DEB_URL:-https://dl.influxdata.com/telegraf/releases/telegraf_${TELEGRAF_VERSION}-1_amd64.deb}"
TELEGRAF_TMP_DEB="/tmp/telegraf_${TELEGRAF_VERSION}_amd64.deb"
TELEGRAF_FORCE_VERSION="${TELEGRAF_FORCE_VERSION:-false}"
MANAGE_DCGM_SERVICE="${GPU_AGENT_MANAGE_DCGM_SERVICE:-false}"
DCGM_EXPORTER_ACTION="install"
GPU_AGENT_LINK_ACTION="install"

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
      echo "Preserving existing Telegraf. Run 'sudo TELEGRAF_FORCE_VERSION=true ./install_linux.sh' to replace it."
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
if [[ ! -f "${DCGM_EXPORTER_TARGET}" ]]; then
  cp dcgm-exporter "${DCGM_EXPORTER_TARGET}"
  chmod +x "${DCGM_EXPORTER_TARGET}"
elif ! cmp -s dcgm-exporter "${DCGM_EXPORTER_TARGET}"; then
  if [[ "${MANAGE_DCGM_SERVICE}" == "true" ]]; then
    cp "${DCGM_EXPORTER_TARGET}" "${DCGM_EXPORTER_TARGET}.gpu-agent.bak"
    cp dcgm-exporter "${DCGM_EXPORTER_TARGET}"
    chmod +x "${DCGM_EXPORTER_TARGET}"
    DCGM_EXPORTER_ACTION="replace"
    echo "Replaced existing dcgm-exporter binary and backed up the previous file."
  else
    DCGM_EXPORTER_ACTION="preserve"
    echo "Existing dcgm-exporter binary differs from bundled version; preserving it."
    echo "Run 'sudo GPU_AGENT_MANAGE_DCGM_SERVICE=true ./install_linux.sh' to replace it."
  fi
fi
if [[ ! -f "${SYSTEMD_DIR}/dcgm-exporter.service" ]]; then
  cp dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"
elif ! cmp -s dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"; then
  if [[ "${MANAGE_DCGM_SERVICE}" == "true" ]]; then
    cp "${SYSTEMD_DIR}/dcgm-exporter.service" "${SYSTEMD_DIR}/dcgm-exporter.service.gpu-agent.bak"
    cp dcgm-exporter.service "${SYSTEMD_DIR}/dcgm-exporter.service"
    echo "Replaced existing dcgm-exporter.service and backed up the previous file."
  else
    echo "Existing dcgm-exporter.service differs from bundled unit; preserving it."
    echo "Run 'sudo GPU_AGENT_MANAGE_DCGM_SERVICE=true ./install_linux.sh' to replace it."
  fi
fi

cat > "${BIN_DIR}/gpu-agent" <<'WRAP'
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=/opt/gpu-agent/pkg
exec python3 -m gpu_agent.main "$@"
WRAP
chmod +x "${BIN_DIR}/gpu-agent"

if [[ -L "${AGENT_LINK_TARGET}" ]]; then
  CURRENT_LINK_TARGET="$(readlink "${AGENT_LINK_TARGET}")"
  if [[ "${CURRENT_LINK_TARGET}" != "${BIN_DIR}/gpu-agent" ]]; then
    GPU_AGENT_LINK_ACTION="preserve"
    echo "Existing gpu-agent symlink points to ${CURRENT_LINK_TARGET}; preserving it."
  fi
elif [[ -e "${AGENT_LINK_TARGET}" ]]; then
  GPU_AGENT_LINK_ACTION="preserve"
  echo "Existing ${AGENT_LINK_TARGET} is not a managed symlink; preserving it."
else
  ln -s "${BIN_DIR}/gpu-agent" "${AGENT_LINK_TARGET}"
fi

if [[ "${GPU_AGENT_LINK_ACTION}" != "preserve" ]]; then
  ln -sfn "${BIN_DIR}/gpu-agent" "${AGENT_LINK_TARGET}"
fi

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
systemctl enable dcgm-exporter
systemctl restart dcgm-exporter
systemctl enable gpu-agent-validate.timer
systemctl start gpu-agent-validate.timer

echo "Installed. Next steps:"
if [[ "${TELEGRAF_ACTION}" == "preserve" ]]; then
  echo "  - preserved existing telegraf installation"
elif [[ "${TELEGRAF_ACTION}" == "replace" ]]; then
  echo "  - replaced telegraf with version ${TELEGRAF_VERSION}"
fi
if [[ "${DCGM_EXPORTER_ACTION}" == "preserve" ]]; then
  echo "  - preserved existing dcgm-exporter binary"
elif [[ "${DCGM_EXPORTER_ACTION}" == "replace" ]]; then
  echo "  - replaced dcgm-exporter binary with bundled version"
else
  echo "  - installed bundled dcgm-exporter binary"
fi
if [[ "${GPU_AGENT_LINK_ACTION}" == "preserve" ]]; then
  echo "  - preserved existing /usr/local/bin/gpu-agent"
else
  echo "  - linked /usr/local/bin/gpu-agent to ${BIN_DIR}/gpu-agent"
fi
echo "  1) sudo gpu-agent validate"
echo "  2) sudo cat /var/log/gpu-agent/last_result.json"
echo "     - non-root validate is supported, but the default guide uses sudo for consistency"
