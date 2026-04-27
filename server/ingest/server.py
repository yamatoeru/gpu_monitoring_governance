from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .clickhouse import insert_records, is_enabled as clickhouse_enabled
from .normalizer import normalize_payload


HOST = os.getenv("INGEST_HOST", "0.0.0.0")
PORT = int(os.getenv("INGEST_PORT", "8080"))
OUTPUT_PATH = os.getenv("INGEST_OUTPUT_PATH", "")


def _append_ndjson(records: list[dict]) -> None:
    if not OUTPUT_PATH:
        return
    path = Path(OUTPUT_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "GPUIngest/0.1"

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/events":
            self._send_json(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": "invalid_json", "detail": str(exc)})
            return

        normalized = normalize_payload(payload)
        for record in normalized:
            print(json.dumps(record, ensure_ascii=False), flush=True)
        _append_ndjson(normalized)
        try:
            insert_records(normalized)
        except RuntimeError as exc:
            self._send_json(502, {"error": "clickhouse_insert_failed", "detail": str(exc)})
            return

        self._send_json(200, {"accepted": len(normalized)})

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> None:
    httpd = HTTPServer((HOST, PORT), Handler)
    print(
        json.dumps(
                {
                    "status": "starting",
                    "host": HOST,
                    "port": PORT,
                    "output_path": OUTPUT_PATH,
                    "clickhouse_enabled": clickhouse_enabled(),
                },
                ensure_ascii=False,
            ),
        flush=True,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
