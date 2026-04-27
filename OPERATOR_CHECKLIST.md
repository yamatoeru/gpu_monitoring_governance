# 운영자 배포 체크리스트

이 문서는 운영자가 중앙 수집 계층과 환경별 배포 준비를 할 때 확인해야 할 항목을 정리한 체크리스트입니다.

## 1. 아키텍처 확인

- 메트릭 경로와 로그/이벤트 경로를 분리했는지 확인
- Kubernetes / Linux GPU 노드에서는 `dcgm-exporter -> vmagent -> VictoriaMetrics` 경로를 사용
- Kubernetes / Linux GPU 노드에서는 `telegraf -> ingest -> ClickHouse` 경로를 사용
- Windows 노드에서는 `telegraf`가 메트릭과 로그를 모두 생성하고, 메트릭은 `vmagent`가 scrape하도록 설계
- `gpu-ingest`는 수신 게이트웨이이며, 현재 리포 기준으로는 normalize 후 ClickHouse HTTP insert를 수행할 수 있다는 점을 운영 범위에 반영

## 2. 중앙 수집 계층 준비

### VictoriaMetrics / vmagent

- `vmagent` 배포 위치와 scrape 대상 범위를 확정
- Kubernetes GPU 노드의 `dcgm-exporter` scrape job을 정의
- Windows Telegraf metrics endpoint scrape job을 정의
- 레이블 체계를 확정
  - `client_id`
  - `cluster`
  - `host`
  - `env_type`
  - `component`
- retention / remote write / auth 정책을 확정

### ClickHouse

- 이벤트 저장용 DB / table 생성 계획 수립
- normalized event 스키마 확정
- partition key / order key / TTL 정책 확정
- 운영 계정과 접근 제어 정책 확정
- 초기 DDL은 [ingest/README.md](ingest/README.md) 의 `ClickHouse 스키마 예시`를 기준으로 시작

### ingest

- `gpu-ingest`를 서버 클러스터 / 네임스페이스에 배치
- `Service` 주소와 DNS 명세 확정
- 필요 시 `gpu-ingest` 앞단에 `Envoy Gateway`를 두고, 클라이언트는 Gateway endpoint만 사용하도록 표준화
- `CLICKHOUSE_URL`, `CLICKHOUSE_DATABASE`, `CLICKHOUSE_TABLE`, 인증 정보 전달 방식 확정
- Kubernetes에서는 `gpu-ingest-clickhouse` Secret 키 구성을 표준화
- 운영 배포는 `k8s/server` 기준으로 수행하고, `python3 -m ingest.server`는 개발/로컬 테스트 용도로만 사용
- readiness / liveness probe 정책 확인
- stdout log 수집 여부 결정
- 내부 version endpoint URL과 DNS 해석 가능 범위를 확정

## 3. 네트워크 / 보안

- 클라이언트 환경에서 `ingest` URL 접근 가능 여부 확인
- `Envoy Gateway`를 사용하는 경우 `ingest_url`은 `gpu-ingest` Service가 아니라 Gateway URL을 가리키게 구성
- 클라이언트 환경에서 `vmagent` scrape 또는 remote write 경로 접근 가능 여부 확인
- 방화벽 / NetworkPolicy / 사내 프록시 정책 확인
- 필요 시 TLS termination 위치 결정
- `Envoy Gateway` 사용 시 TLS termination, header 기반 인증, body size 제한, request timeout, rate limit 정책을 Gateway에 둘지 확정
- 토큰 / 헤더 기반 인증이 필요한 경우 전달 방식 정의

## 4. Kubernetes 운영 준비

- `gpu-monitoring` 네임스페이스 사용 여부 결정
- `dcgm-exporter`, `telegraf`, `validator`, `gpu-ingest` 배포 기준 정리
- GPU 노드 라벨 / nodeSelector / toleration 정책 확인
- `vmagent`가 `dcgm-exporter`를 scrape하도록 별도 매니페스트 또는 기존 운영 스택 반영
- `telegraf`가 컨테이너 로그를 읽을 수 있도록 `/var/log/containers`, `/var/log/pods` 마운트 확인
- `validator` CronJob 스케줄과 실패 보존 정책 확인
- `gpu-ingest` Service DNS를 `ingest_url`에 반영

### Envoy Gateway 사용 시 추가 확인

- `gpu-ingest`는 내부 `ClusterIP`로 두고, 외부 노출은 `Envoy Gateway`를 통해서만 수행할지 결정
- Gateway route는 `POST /events`를 `gpu-ingest` Service로 전달하도록 구성
- 필요 시 `GET /health`도 운영 점검용으로 노출할지 결정
- Gateway timeout이 `validator` / `telegraf`의 전송 timeout보다 과도하게 짧지 않은지 확인
- `telegraf` payload를 고려해 request body size 제한을 확인
- retry를 Gateway에서 할지, sender에서만 할지 정책을 분리
- 클라이언트 설정(`GPU_AGENT_INGEST_URL`, K8s `ingest_url`)은 Gateway URL만 사용하도록 통일

## 5. Linux 운영 준비

- Python 3.10+ 설치 여부 확인
- NVIDIA 드라이버 / `nvidia-smi` 동작 여부 확인
- 기본 번들 `dcgm-exporter` 호환 바이너리를 사용할지, 기존 운영 바이너리로 대체할지 결정
- `telegraf` 자동 설치가 허용되는지 확인
- 폐쇄망이면 `TELEGRAF_DEB_URL` 사내 미러 경로 준비
- 테스트 단계에서는 기본 GitHub raw URL 사용 가능 여부 확인
- 운영 단계에서는 `GPU_AGENT_LATEST_VERSION_URL`이 가리킬 내부 version endpoint 준비
- systemd 서비스 정책과 로그 보관 경로 확인

## 6. Windows 운영 준비

- Python 3.10+ 설치 여부 확인
- PowerShell 실행 정책 예외 절차 공유
- Telegraf ZIP 다운로드 허용 여부 확인
- 폐쇄망이면 `TELEGRAF_ZIP_URL` 사내 배포 경로 준비
- 테스트 단계에서는 기본 GitHub raw URL 사용 가능 여부 확인
- 운영 단계에서는 `GPU_AGENT_LATEST_VERSION_URL`이 가리킬 내부 version endpoint 준비
- OpenSSH 또는 RDP 운영 접근 방식 확정
- Windows Event Log / 서비스 상태 수집 범위 정의

## 7. 배포 전 최종 점검

- README / USER_GUIDE / TROUBLESHOOTING 문서 최신 상태 확인
- 환경별 `ingest_url`과 메트릭 경로가 올바르게 분리되어 있는지 확인
- 테스트 클러스터와 운영 클러스터 오버레이를 구분했는지 확인
- `fake-ingest` 같은 테스트 전용 리소스가 운영 배포 경로에 남아 있지 않은지 확인

## 8. 배포 후 검증

### Kubernetes

- `kubectl get pods -n gpu-monitoring`
- `kubectl get ds -n gpu-monitoring`
- `kubectl get cronjob -n gpu-monitoring`
- `kubectl logs -n gpu-monitoring deployment/gpu-ingest --tail=50`
- 수동 validator job 실행 후 `gpu-ingest` 수신 확인
- ClickHouse table row 증가 여부 확인
- `Envoy Gateway`를 쓰는 경우 Gateway access log / route status / upstream 5xx 여부 확인

### Linux

- `sudo /opt/gpu-agent/bin/gpu-agent validate`
- `/var/log/gpu-agent/last_result.json` 확인
- `systemctl status telegraf` 확인
- `systemctl status dcgm-exporter` 확인
- `curl http://127.0.0.1:9400/metrics`에서 `DCGM_FI_DEV_GPU_UTIL` 확인

### Windows

- `C:\gpu-agent\bin\gpu-agent.cmd validate`
- `C:\gpu-agent\status\last_result.json` 확인
- `Get-Service telegraf` 확인
- `where.exe nvidia-smi` / `nvidia-smi` 확인

### ClickHouse 점검 쿼리

기본 테이블:

```sql
SELECT count()
FROM gpu_monitoring.events;
```

최근 이벤트 확인:

```sql
SELECT
    event_time,
    source,
    host,
    component,
    event_type,
    severity,
    error_code
FROM gpu_monitoring.events
ORDER BY event_time DESC
LIMIT 50;
```

최근 실패 이벤트만 확인:

```sql
SELECT
    event_time,
    host,
    component,
    event_type,
    error_code,
    message,
    root_cause,
    recommended_action
FROM gpu_monitoring.events
WHERE severity = 'error'
ORDER BY event_time DESC
LIMIT 50;
```

호스트별 최근 이벤트 건수:

```sql
SELECT
    host,
    count() AS event_count
FROM gpu_monitoring.events
WHERE event_time >= toString(now() - INTERVAL 1 DAY)
GROUP BY host
ORDER BY event_count DESC;
```

이벤트 유형별 건수:

```sql
SELECT
    event_type,
    error_code,
    count() AS event_count
FROM gpu_monitoring.events
WHERE event_time >= toString(now() - INTERVAL 1 DAY)
GROUP BY event_type, error_code
ORDER BY event_count DESC;
```

특정 호스트의 최근 validator 결과:

```sql
SELECT
    event_time,
    event_type,
    error_code,
    message
FROM gpu_monitoring.events
WHERE component = 'gpu-agent-validator'
  AND host = '<host>'
ORDER BY event_time DESC
LIMIT 20;
```

성공/실패 추이 단순 확인:

```sql
SELECT
    severity,
    count() AS event_count
FROM gpu_monitoring.events
WHERE event_time >= toString(now() - INTERVAL 1 DAY)
GROUP BY severity
ORDER BY event_count DESC;
```

참고:

- 현재 `event_time` 컬럼은 `String` 입니다.
- 운영 고도화 시에는 `DateTime` 계열과 파티션 키를 포함한 스키마로 확장하는 것이 좋습니다.
- 현재 기본 DDL은 [ingest/README.md](ingest/README.md) 에 있습니다.

## 9. 현재 남은 운영 작업

- 인증 / 고객 식별 / dedup / retry 정책 추가
- 운영 대시보드와 알림 룰 연결
- 장기 보관 및 재처리 전략 정리
