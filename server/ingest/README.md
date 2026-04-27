# Ingest Gateway

최소 ingest gateway 초안입니다.

역할:

- `gpu-agent` / `validator`가 직접 보내는 JSON 이벤트 수신
- `telegraf`가 보내는 `metrics` 배열 payload 수신
- 두 입력을 공통 normalized event 형태로 변환
- stdout 또는 NDJSON 파일로 기록

현재 범위:

- normalize 수행
- 선택적으로 ClickHouse HTTP insert 수행
- 운영용 인증 / dedup / retry / dead-letter queue는 아직 미구현

## 운영 배포

운영 기준으로는 `ingest`를 서버측 Kubernetes 클러스터에 배포합니다.

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone server/k8s | kubectl apply -f -
```

클라이언트 클러스터는 `validator`/`telegraf`가 아래 endpoint로 전송하도록 설정합니다.

```text
http://<server-cluster-gpu-ingest-loadbalancer>:8080/events
```

Kubernetes에서는 `gpu-ingest-clickhouse` Secret에 아래 ClickHouse 키를 넣어 `gpu-ingest` Deployment에 주입합니다.

## 로컬 개발 실행

```bash
cd server
python3 -m ingest.server
```

환경변수:

- `INGEST_HOST`
  기본값: `0.0.0.0`
- `INGEST_PORT`
  기본값: `8080`
- `INGEST_OUTPUT_PATH`
  설정 시 normalized event를 NDJSON 파일로 추가 기록
- `CLICKHOUSE_URL`
  설정 시 normalized event를 ClickHouse HTTP API로 insert
- `CLICKHOUSE_DATABASE`
  기본값: `gpu_monitoring`
- `CLICKHOUSE_TABLE`
  기본값: `events`
- `CLICKHOUSE_USER`
  Basic auth 사용자명
- `CLICKHOUSE_PASSWORD`
  Basic auth 비밀번호
- `CLICKHOUSE_TIMEOUT`
  기본값: `5`

예:

```bash
INGEST_OUTPUT_PATH=/tmp/gpu-monitoring-events.ndjson python3 -m ingest.server
```

로컬 개발에서 ClickHouse insert까지 함께 쓰려면:

```bash
CLICKHOUSE_URL=http://clickhouse.monitoring.svc.cluster.local:8123 \
CLICKHOUSE_DATABASE=gpu_monitoring \
CLICKHOUSE_TABLE=events \
python3 -m ingest.server
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

## ClickHouse 스키마 예시

```sql
CREATE DATABASE IF NOT EXISTS gpu_monitoring;

CREATE TABLE IF NOT EXISTS gpu_monitoring.events
(
    event_time String,
    source String,
    host String,
    env_type String,
    os_type String,
    component String,
    event_type String,
    severity String,
    error_code String,
    message String,
    root_cause String,
    recommended_action String,
    agent_version String,
    config_version String,
    stream String,
    logtag String,
    path String,
    checks_json String,
    extra_json String,
    raw_payload_json String,
    raw_metric_json String
)
ENGINE = MergeTree
ORDER BY (event_time, host, component, event_type);
```

## 다음 단계

- 인증 토큰 검증
- 중복 제거 키 생성
- dead-letter queue / retry 추가
