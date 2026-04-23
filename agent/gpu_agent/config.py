from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    env_type: str = "vm"
    config_version: str = "2026.04.23"
    latest_version_url: str = "http://repo.internal/gpu-agent/latest_version.json"
    ingest_url: str = ""
    ingest_token: str = ""
    linux_result_dir: str = "/var/log/gpu-agent"
    windows_result_dir: str = r"C:\gpu-agent\status"
    dcgm_metrics_url: str = "http://127.0.0.1:9400/metrics"
    telegraf_service_linux: str = "telegraf"
    dcgm_service_linux: str = "dcgm-exporter"
    telegraf_service_windows: str = "telegraf"
    heartbeat_file_name: str = "heartbeat.json"

    @property
    def result_dir(self) -> Path:
        if platform.system().lower().startswith("win"):
            return Path(self.windows_result_dir)
        return Path(self.linux_result_dir)


def load_config() -> AgentConfig:
    return AgentConfig(
        env_type=os.getenv("GPU_AGENT_ENV_TYPE", "vm"),
        config_version=os.getenv("GPU_AGENT_CONFIG_VERSION", "2026.04.23"),
        latest_version_url=os.getenv(
            "GPU_AGENT_LATEST_VERSION_URL",
            "http://repo.internal/gpu-agent/latest_version.json",
        ),
        ingest_url=os.getenv("GPU_AGENT_INGEST_URL", ""),
        ingest_token=os.getenv("GPU_AGENT_INGEST_TOKEN", ""),
        linux_result_dir=os.getenv("GPU_AGENT_RESULT_DIR_LINUX", "/var/log/gpu-agent"),
        windows_result_dir=os.getenv("GPU_AGENT_RESULT_DIR_WINDOWS", r"C:\gpu-agent\status"),
        dcgm_metrics_url=os.getenv(
            "GPU_AGENT_DCGM_METRICS_URL",
            "http://127.0.0.1:9400/metrics",
        ),
        telegraf_service_linux=os.getenv("GPU_AGENT_TELEGRAF_SERVICE_LINUX", "telegraf"),
        dcgm_service_linux=os.getenv("GPU_AGENT_DCGM_SERVICE_LINUX", "dcgm-exporter"),
        telegraf_service_windows=os.getenv("GPU_AGENT_TELEGRAF_SERVICE_WINDOWS", "telegraf"),
    )
