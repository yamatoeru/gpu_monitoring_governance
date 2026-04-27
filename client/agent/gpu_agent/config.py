from __future__ import annotations

import os
import platform
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _default_env_file() -> Path:
    if platform.system().lower().startswith("win"):
        return Path(r"C:\gpu-agent\agent.env")
    sysconfig = Path("/etc/sysconfig/gpu-agent")
    if sysconfig.exists():
        return sysconfig
    return Path("/etc/default/gpu-agent")


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


def _default_linux_result_dir() -> tuple[str, str]:
    preferred = Path("/var/log/gpu-agent")
    env_override = os.getenv("GPU_AGENT_RESULT_DIR_LINUX")
    if env_override:
        return env_override, ""

    if preferred.exists() and os.access(preferred, os.W_OK):
        return str(preferred), ""

    if preferred.parent.exists() and os.access(preferred.parent, os.W_OK):
        return str(preferred), ""

    fallback = Path(tempfile.gettempdir()) / f"gpu-agent-{os.getenv('USER', 'user')}"
    notice = (
        f"result directory '{preferred}' is not writable; "
        f"using '{fallback}' for this run"
    )
    return str(fallback), notice


@dataclass
class AgentConfig:
    env_type: str = "vm"
    config_version: str = "2026.04.23"
    latest_version_url: str = "https://raw.githubusercontent.com/yamatoeru/gpu_monitoring_governance/main/examples/latest_version.json"
    ingest_url: str = ""
    ingest_token: str = ""
    linux_result_dir: str = "/var/log/gpu-agent"
    windows_result_dir: str = r"C:\gpu-agent\status"
    dcgm_metrics_url: str = "http://127.0.0.1:9400/metrics"
    telegraf_service_linux: str = "telegraf"
    dcgm_service_linux: str = "dcgm-exporter"
    telegraf_service_windows: str = "telegraf"
    heartbeat_file_name: str = "heartbeat.json"
    result_dir_notice: str = ""

    @property
    def result_dir(self) -> Path:
        if platform.system().lower().startswith("win"):
            return Path(self.windows_result_dir)
        return Path(self.linux_result_dir)


def load_config() -> AgentConfig:
    env_file = Path(os.getenv("GPU_AGENT_ENV_FILE", str(_default_env_file())))
    _load_env_file(env_file)
    linux_result_dir, result_dir_notice = _default_linux_result_dir()

    return AgentConfig(
        env_type=os.getenv("GPU_AGENT_ENV_TYPE", "vm"),
        config_version=os.getenv("GPU_AGENT_CONFIG_VERSION", "2026.04.23"),
        latest_version_url=os.getenv(
            "GPU_AGENT_LATEST_VERSION_URL",
            "https://raw.githubusercontent.com/yamatoeru/gpu_monitoring_governance/main/examples/latest_version.json",
        ),
        ingest_url=os.getenv("GPU_AGENT_INGEST_URL", ""),
        ingest_token=os.getenv("GPU_AGENT_INGEST_TOKEN", ""),
        linux_result_dir=linux_result_dir,
        windows_result_dir=os.getenv("GPU_AGENT_RESULT_DIR_WINDOWS", r"C:\gpu-agent\status"),
        dcgm_metrics_url=os.getenv(
            "GPU_AGENT_DCGM_METRICS_URL",
            "http://127.0.0.1:9400/metrics",
        ),
        telegraf_service_linux=os.getenv("GPU_AGENT_TELEGRAF_SERVICE_LINUX", "telegraf"),
        dcgm_service_linux=os.getenv("GPU_AGENT_DCGM_SERVICE_LINUX", "dcgm-exporter"),
        telegraf_service_windows=os.getenv("GPU_AGENT_TELEGRAF_SERVICE_WINDOWS", "telegraf"),
        result_dir_notice=result_dir_notice,
    )
