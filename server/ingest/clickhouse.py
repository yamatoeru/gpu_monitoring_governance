from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request


CLICKHOUSE_URL = os.getenv("CLICKHOUSE_URL", "").rstrip("/")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "gpu_monitoring")
CLICKHOUSE_TABLE = os.getenv("CLICKHOUSE_TABLE", "events")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_TIMEOUT = float(os.getenv("CLICKHOUSE_TIMEOUT", "5"))

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_COLUMNS = [
    "event_time",
    "source",
    "host",
    "env_type",
    "os_type",
    "component",
    "event_type",
    "severity",
    "error_code",
    "message",
    "root_cause",
    "recommended_action",
    "agent_version",
    "config_version",
    "stream",
    "logtag",
    "path",
    "checks_json",
    "extra_json",
    "raw_payload_json",
    "raw_metric_json",
]


def is_enabled() -> bool:
    return bool(CLICKHOUSE_URL)


def _validate_identifier(value: str, label: str) -> str:
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(f"invalid_clickhouse_{label}")
    return value


def _json_string(value: object) -> str:
    if value in (None, ""):
        return ""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _prepare_record(record: dict) -> dict[str, str]:
    prepared = {
        "event_time": str(record.get("event_time", "")),
        "source": str(record.get("source", "")),
        "host": str(record.get("host", "")),
        "env_type": str(record.get("env_type", "")),
        "os_type": str(record.get("os_type", "")),
        "component": str(record.get("component", "")),
        "event_type": str(record.get("event_type", "")),
        "severity": str(record.get("severity", "")),
        "error_code": str(record.get("error_code", "")),
        "message": str(record.get("message", "")),
        "root_cause": str(record.get("root_cause", "")),
        "recommended_action": str(record.get("recommended_action", "")),
        "agent_version": str(record.get("agent_version", "")),
        "config_version": str(record.get("config_version", "")),
        "stream": str(record.get("stream", "")),
        "logtag": str(record.get("logtag", "")),
        "path": str(record.get("path", "")),
        "checks_json": _json_string(record.get("checks")),
        "extra_json": _json_string(record.get("extra")),
        "raw_payload_json": _json_string(record.get("raw_payload")),
        "raw_metric_json": _json_string(record.get("raw_metric")),
    }
    return {column: prepared[column] for column in _COLUMNS}


def insert_records(records: list[dict]) -> None:
    if not records or not is_enabled():
        return

    database = _validate_identifier(CLICKHOUSE_DATABASE, "database")
    table = _validate_identifier(CLICKHOUSE_TABLE, "table")
    query = f"INSERT INTO {database}.{table} FORMAT JSONEachRow"
    endpoint = f"{CLICKHOUSE_URL}/?query={urllib.parse.quote(query, safe='')}"
    body = "\n".join(
        json.dumps(_prepare_record(record), ensure_ascii=False, separators=(",", ":"))
        for record in records
    ).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-ndjson; charset=utf-8"},
    )
    password_manager = None
    if CLICKHOUSE_USER:
        password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(
            None,
            CLICKHOUSE_URL,
            CLICKHOUSE_USER,
            CLICKHOUSE_PASSWORD,
        )
    opener = urllib.request.build_opener(
        urllib.request.HTTPBasicAuthHandler(password_manager) if password_manager else urllib.request.BaseHandler()
    )
    try:
        with opener.open(request, timeout=CLICKHOUSE_TIMEOUT) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"clickhouse_http_{exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"clickhouse_unreachable: {exc.reason}") from exc
