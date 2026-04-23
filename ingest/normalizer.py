from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _to_iso_from_epoch(value: Any) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).astimezone().isoformat()
    return _now_iso()


def _safe_json_loads(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith("{"):
        return None
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _infer_component_from_path(path: str) -> str:
    if "validator" in path:
        return "gpu-agent-validator"
    if "dcgm-exporter" in path:
        return "dcgm-exporter"
    if "telegraf" in path:
        return "telegraf"
    return "unknown"


def normalize_direct_event(payload: dict[str, Any]) -> list[dict[str, Any]]:
    event_time = payload.get("event_time") or _now_iso()
    normalized = {
        "event_time": event_time,
        "source": "direct",
        "host": payload.get("host", ""),
        "env_type": payload.get("env_type", ""),
        "os_type": payload.get("os_type", ""),
        "component": payload.get("component", "unknown"),
        "event_type": payload.get("event_type", "unknown"),
        "severity": payload.get("severity", "info"),
        "error_code": payload.get("error_code", ""),
        "message": payload.get("message", ""),
        "root_cause": payload.get("root_cause", ""),
        "recommended_action": payload.get("recommended_action", ""),
        "agent_version": payload.get("agent_version", ""),
        "config_version": payload.get("config_version", ""),
        "stream": "",
        "logtag": "",
        "raw_payload": payload,
    }
    if "checks" in payload:
        normalized["checks"] = payload["checks"]
    if "extra" in payload:
        normalized["extra"] = payload["extra"]
    return [normalized]


def normalize_telegraf_metric(metric: dict[str, Any]) -> dict[str, Any]:
    tags = metric.get("tags", {}) or {}
    fields = metric.get("fields", {}) or {}
    raw_message = fields.get("message", "")
    parsed_message = _safe_json_loads(raw_message)

    component = tags.get("component") or (parsed_message or {}).get("component")
    if not component:
        component = _infer_component_from_path(tags.get("path", ""))

    event_type = tags.get("event_type") or (parsed_message or {}).get("event_type")
    severity = tags.get("severity") or (parsed_message or {}).get("severity", "info")
    error_code = tags.get("error_code") or (parsed_message or {}).get("error_code", "")
    env_type = tags.get("env_type") or (parsed_message or {}).get("env_type", "k8s")
    os_type = tags.get("os_type") or (parsed_message or {}).get("os_type", "kubernetes")
    host = (parsed_message or {}).get("host") or tags.get("host", "")
    event_time = (
        (parsed_message or {}).get("event_time")
        or fields.get("cri_time")
        or _to_iso_from_epoch(metric.get("timestamp"))
    )
    message = raw_message if raw_message else json.dumps(fields, ensure_ascii=False)

    normalized = {
        "event_time": event_time,
        "source": "telegraf",
        "host": host,
        "env_type": env_type,
        "os_type": os_type,
        "component": component,
        "event_type": event_type or metric.get("name", "unknown"),
        "severity": severity,
        "error_code": error_code,
        "message": message,
        "root_cause": (parsed_message or {}).get("root_cause", ""),
        "recommended_action": (parsed_message or {}).get("recommended_action", ""),
        "agent_version": (parsed_message or {}).get("agent_version", ""),
        "config_version": (parsed_message or {}).get("config_version", ""),
        "stream": tags.get("stream", ""),
        "logtag": tags.get("logtag", ""),
        "path": tags.get("path", ""),
        "raw_metric": metric,
    }
    if parsed_message and "checks" in parsed_message:
        normalized["checks"] = parsed_message["checks"]
    return normalized


def normalize_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "event_time" in payload and "event_type" in payload:
        return normalize_direct_event(payload)

    metrics = payload.get("metrics")
    if isinstance(metrics, list):
        return [normalize_telegraf_metric(metric) for metric in metrics if isinstance(metric, dict)]

    return [{
        "event_time": _now_iso(),
        "source": "unknown",
        "host": "",
        "env_type": "",
        "os_type": "",
        "component": "ingest",
        "event_type": "unclassified_payload",
        "severity": "warning",
        "error_code": "UNCLASSIFIED",
        "message": json.dumps(payload, ensure_ascii=False),
        "root_cause": "",
        "recommended_action": "inspect raw_payload",
        "agent_version": "",
        "config_version": "",
        "stream": "",
        "logtag": "",
        "raw_payload": payload,
    }]
