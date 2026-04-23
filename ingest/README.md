# Ingest Gateway

최소 ingest gateway 초안입니다.

역할:

- `gpu-agent` / `validator`가 직접 보내는 JSON 이벤트 수신
- `telegraf`가 보내는 `metrics` 배열 payload 수신
- 두 입력을 공통 normalized event 형태로 변환
- stdout 또는 NDJSON 파일로 기록

## 실행

```bash
cd ingest
python3 -m ingest.server
```

환경변수:

- `INGEST_HOST`
  기본값: `0.0.0.0`
- `INGEST_PORT`
  기본값: `8080`
- `INGEST_OUTPUT_PATH`
  설정 시 normalized event를 NDJSON 파일로 추가 기록

예:

```bash
INGEST_OUTPUT_PATH=/tmp/gpu-monitoring-events.ndjson python3 -m ingest.server
```

## 엔드포인트

- `GET /health`
- `POST /events`

## Normalize 결과 예시

direct event:

```json
{
  "event_time": "2026-04-24T00:00:00+09:00",
  "source": "direct",
  "host": "manual-validator-123",
  "env_type": "k8s",
  "os_type": "kubernetes",
  "component": "gpu-agent-validator",
  "event_type": "k8s_validation_passed",
  "severity": "info",
  "error_code": "OK",
  "message": "k8s validation passed"
}
```

telegraf event:

```json
{
  "event_time": "2026-04-24T00:00:00.000000000Z",
  "source": "telegraf",
  "host": "manual-validator-123",
  "env_type": "k8s",
  "os_type": "kubernetes",
  "component": "gpu-agent-validator",
  "event_type": "k8s_validation_passed",
  "severity": "info",
  "error_code": "OK",
  "message": "{\"event_time\":\"...\",\"event_type\":\"k8s_validation_passed\"}",
  "stream": "stdout",
  "logtag": "F"
}
```

## 다음 단계

- ClickHouse HTTP insert 추가
- VictoriaMetrics remote write 또는 metrics passthrough 분리
- 인증 토큰 검증
- 중복 제거 키 생성
- dead-letter queue / retry 추가
