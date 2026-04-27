from __future__ import annotations

import json
import urllib.request

from .config import AgentConfig
from .utils import dump_json, now_iso


def infer_root_cause(check_name: str) -> str:
    mapping = {
        "nvidia_smi": "nvidia driver missing or broken",
        "dcgm_metrics": "dcgm exporter metrics unavailable",
        "service_telegraf": "telegraf service not running",
        "service_dcgm-exporter": "dcgm exporter service not running",
        "agent_version": "agent is outdated or version endpoint is unavailable",
        "telegraf_version_linux": "installed telegraf version differs from approved version",
        "telegraf_version_windows": "installed telegraf version differs from approved version",
        "dcgm_exporter_version_linux": "installed dcgm-exporter version differs from approved version",
    }
    return mapping.get(check_name, "unknown")


def infer_action(check_name: str) -> str:
    mapping = {
        "nvidia_smi": "install or fix NVIDIA driver, then rerun gpu-agent validate",
        "dcgm_metrics": "verify dcgm-exporter and run gpu-agent repair",
        "service_telegraf": "run gpu-agent repair",
        "service_dcgm-exporter": "run gpu-agent repair or restart dcgm-exporter",
        "agent_version": "run gpu-agent upgrade",
        "telegraf_version_linux": "update telegraf to the approved version and rerun gpu-agent validate",
        "telegraf_version_windows": "update telegraf to the approved version and rerun gpu-agent validate",
        "dcgm_exporter_version_linux": "update dcgm-exporter to the approved version and rerun gpu-agent validate",
    }
    return mapping.get(check_name, "run gpu-agent validate")


def build_event(host: str, env_type: str, os_type: str, agent_version: str, config_version: str,
                event_type: str, severity: str, error_code: str, message: str,
                root_cause: str = "", recommended_action: str = "", checks: list | None = None,
                extra: dict | None = None) -> dict:
    return {
        "event_time": now_iso(),
        "host": host,
        "env_type": env_type,
        "os_type": os_type,
        "component": "gpu-agent",
        "event_type": event_type,
        "severity": severity,
        "error_code": error_code,
        "message": message,
        "root_cause": root_cause,
        "recommended_action": recommended_action,
        "agent_version": agent_version,
        "config_version": config_version,
        "checks": checks or [],
        "extra": extra or {},
    }


def build_validation_event(host: str, env_type: str, os_type: str, agent_version: str, config_version: str,
                           checks: list[dict]) -> tuple[dict, int]:
    failed = [c for c in checks if not c.get("ok")]
    if not failed:
        return build_event(
            host=host,
            env_type=env_type,
            os_type=os_type,
            agent_version=agent_version,
            config_version=config_version,
            event_type="validation_passed",
            severity="info",
            error_code="OK",
            message="validation passed",
            recommended_action="none",
            checks=checks,
        ), 0

    primary = failed[0]
    return build_event(
        host=host,
        env_type=env_type,
        os_type=os_type,
        agent_version=agent_version,
        config_version=config_version,
        event_type="validation_failed",
        severity="error",
        error_code=primary["name"].upper(),
        message=primary["message"],
        root_cause=infer_root_cause(primary["name"]),
        recommended_action=infer_action(primary["name"]),
        checks=checks,
    ), 2


def write_event(config: AgentConfig, event: dict, filename: str = "last_result.json") -> None:
    dump_json(config.result_dir / filename, event)


def write_heartbeat(config: AgentConfig, host: str, env_type: str, os_type: str,
                    agent_version: str, config_version: str) -> None:
    payload = build_event(
        host=host,
        env_type=env_type,
        os_type=os_type,
        agent_version=agent_version,
        config_version=config_version,
        event_type="heartbeat",
        severity="info",
        error_code="HEARTBEAT",
        message="heartbeat",
        recommended_action="none",
    )
    dump_json(config.result_dir / config.heartbeat_file_name, payload)


def post_event(config: AgentConfig, event: dict) -> None:
    if not config.ingest_url:
        return
    body = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        config.ingest_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {config.ingest_token}"} if config.ingest_token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=5):
        return


def print_summary(event: dict) -> None:
    print(f"[GPU Agent] {event['severity'].upper()} - {event['event_type']}")
    print(f"Host: {event['host']}")
    print(f"Message: {event['message']}")
    if event.get("root_cause"):
        print(f"Cause: {event['root_cause']}")
    if event.get("recommended_action"):
        print(f"Action: {event['recommended_action']}")
    print(f"Agent version: {event['agent_version']}")
    print(f"Config version: {event['config_version']}")
