from __future__ import annotations

import json
import platform
import urllib.request

from .config import AgentConfig
from .runners import run, run_powershell


def check_platform() -> dict:
    return {
        "name": "platform",
        "ok": True,
        "value": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "message": "platform collected",
    }


def check_nvidia_smi() -> dict:
    res = run(["nvidia-smi"], timeout=10)
    return {
        "name": "nvidia_smi",
        "ok": res.ok,
        "value": res.stdout[:500],
        "message": res.stderr if not res.ok else "nvidia-smi ok",
    }


def check_service(name: str) -> dict:
    if platform.system().lower().startswith("win"):
        res = run_powershell(f"(Get-Service -Name '{name}').Status")
        ok = res.ok and "Running" in res.stdout
        return {
            "name": f"service_{name}",
            "ok": ok,
            "value": res.stdout,
            "message": res.stderr if not ok else "service running",
        }

    res = run(["systemctl", "is-active", name], timeout=10)
    ok = res.ok and res.stdout == "active"
    return {
        "name": f"service_{name}",
        "ok": ok,
        "value": res.stdout,
        "message": res.stderr if not ok else "service active",
    }


def check_dcgm_metrics(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        ok = "DCGM_FI_DEV_GPU_UTIL" in body
        return {
            "name": "dcgm_metrics",
            "ok": ok,
            "value": {"url": url},
            "message": "metric found" if ok else "metric DCGM_FI_DEV_GPU_UTIL not found",
        }
    except Exception as exc:
        return {
            "name": "dcgm_metrics",
            "ok": False,
            "value": {"url": url},
            "message": str(exc),
        }


def check_latest_version(current_version: str, latest_version_url: str) -> dict:
    try:
        with urllib.request.urlopen(latest_version_url, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        latest = payload.get("latest_agent_version", "")
        required = bool(payload.get("required", False))
        ok = (not latest) or (latest == current_version)
        return {
            "name": "agent_version",
            "ok": ok,
            "value": {
                "current_version": current_version,
                "latest_version": latest,
                "required": required,
            },
            "message": "latest" if ok else "outdated",
        }
    except Exception as exc:
        return {
            "name": "agent_version",
            "ok": False,
            "value": {"current_version": current_version},
            "message": f"version check failed: {exc}",
        }


def collect_validation_checks(config: AgentConfig, version: str) -> list[dict]:
    checks = [check_platform(), check_nvidia_smi()]

    if platform.system().lower().startswith("win"):
        checks.append(check_service(config.telegraf_service_windows))
    else:
        checks.append(check_service(config.telegraf_service_linux))
        checks.append(check_service(config.dcgm_service_linux))
        checks.append(check_dcgm_metrics(config.dcgm_metrics_url))

    checks.append(check_latest_version(version, config.latest_version_url))
    return checks
