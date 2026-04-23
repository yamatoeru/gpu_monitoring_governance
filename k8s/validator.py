from __future__ import annotations

import json
import os
import socket
import urllib.request
from datetime import datetime, timezone

from kubernetes import client, config


NAMESPACE = os.getenv("POD_NAMESPACE", "gpu-monitoring")
INGEST_URL = os.getenv("INGEST_URL", "")
DCGM_DS_NAME = os.getenv("DCGM_DS_NAME", "dcgm-exporter")
TELEGRAF_DS_NAME = os.getenv("TELEGRAF_DS_NAME", "telegraf")
AGENT_VERSION = os.getenv("VALIDATOR_VERSION", "0.1.0")
CONFIG_VERSION = os.getenv("CONFIG_VERSION", "2026.04.23")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def read_ds(api: client.AppsV1Api, namespace: str, name: str) -> dict:
    ds = api.read_namespaced_daemon_set(name=name, namespace=namespace)
    desired = ds.status.desired_number_scheduled or 0
    available = ds.status.number_available or 0
    ready = ds.status.number_ready or 0
    return {
        "name": f"daemonset_{name}",
        "ok": desired > 0 and desired == available == ready,
        "value": {
            "desired": desired,
            "available": available,
            "ready": ready,
        },
        "message": "daemonset healthy" if desired > 0 and desired == available == ready else "daemonset unavailable",
    }


def build_event(checks: list[dict]) -> dict:
    failed = [c for c in checks if not c.get("ok")]
    if not failed:
        return {
            "event_time": now_iso(),
            "host": socket.gethostname(),
            "env_type": "k8s",
            "os_type": "kubernetes",
            "component": "gpu-agent-validator",
            "event_type": "k8s_validation_passed",
            "severity": "info",
            "error_code": "OK",
            "message": "k8s validation passed",
            "root_cause": "",
            "recommended_action": "none",
            "agent_version": AGENT_VERSION,
            "config_version": CONFIG_VERSION,
            "checks": checks,
        }
    primary = failed[0]
    return {
        "event_time": now_iso(),
        "host": socket.gethostname(),
        "env_type": "k8s",
        "os_type": "kubernetes",
        "component": "gpu-agent-validator",
        "event_type": "k8s_validation_failed",
        "severity": "error",
        "error_code": primary["name"].upper(),
        "message": primary["message"],
        "root_cause": "daemonset rollout incomplete or unavailable",
        "recommended_action": "check daemonset status and re-apply helm/chart",
        "agent_version": AGENT_VERSION,
        "config_version": CONFIG_VERSION,
        "checks": checks,
    }


def post_event(event: dict) -> None:
    if not INGEST_URL:
        print(json.dumps(event, ensure_ascii=False))
        return
    req = urllib.request.Request(
        INGEST_URL,
        data=json.dumps(event).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5):
        return


def main() -> int:
    config.load_incluster_config()
    apps = client.AppsV1Api()
    checks = [
        read_ds(apps, NAMESPACE, DCGM_DS_NAME),
        read_ds(apps, NAMESPACE, TELEGRAF_DS_NAME),
    ]
    event = build_event(checks)
    post_event(event)
    print(json.dumps(event, ensure_ascii=False))
    return 0 if event["severity"] == "info" else 2


if __name__ == "__main__":
    raise SystemExit(main())
