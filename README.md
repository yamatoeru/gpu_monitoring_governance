# GPU Monitoring Governance Starter Kit

이 리포지토리는 GPU 서버 운영 환경에서 메트릭, 상태, 설치 결과, 장애 이벤트를 표준화해서 수집하기 위한 스타터킷입니다.

현재 기준 아키텍처는 아래를 전제로 합니다.

- Kubernetes / Linux GPU 노드
  - `dcgm-exporter`: GPU 메트릭 노출
  - `vmagent`: `dcgm-exporter` 메트릭 scrape
  - `telegraf`: 로그 / 이벤트 / 상태 정보 전송
  - `validator`: Kubernetes 배포 상태 점검 및 정형 이벤트 전송
- Windows 노드
  - `telegraf`: 메트릭 생성 + 로그 / 이벤트 수집
  - `vmagent`: Windows Telegraf metrics endpoint scrape
- 중앙 수집측
  - `ingest`: direct event / telegraf payload 수신 및 normalize
  - `ClickHouse`: 정형 이벤트 / 로그 저장
  - `VictoriaMetrics`: 시계열 메트릭 저장

## 디렉토리

- `agent/`
  - 공통 Python CLI `gpu-agent`
- `linux/`
  - Linux 설치 스크립트, systemd unit, Telegraf 설정
- `windows/`
  - Windows 설치 스크립트, PowerShell wrapper, Telegraf 설정
- `k8s/`
  - Kubernetes DaemonSet, CronJob, RBAC, ingest 매니페스트
- `k8s/test/`
  - 비GPU 테스트 클러스터용 오버레이
- `ingest/`
  - 최소 ingest gateway 초안
- `examples/`
  - 버전 정보 예시

## 현재 구현 상태

- Linux / Windows 설치 스크립트에 Telegraf 자동 설치 로직이 포함되어 있습니다.
- Kubernetes에서는 `dcgm-exporter`와 `telegraf`가 분리되어 있고, Telegraf는 `dcgm-exporter`를 scrape하지 않습니다.
- Kubernetes `validator`는 direct event를 `ingest`로 전송합니다.
- Kubernetes `telegraf`는 컨테이너 로그를 읽어 `ingest`로 전송하도록 구성돼 있습니다.
- `ingest/`는 direct event와 Telegraf payload를 공통 normalized event로 바꾸는 최소 서버입니다.
- `gpu-ingest` Deployment / Service 매니페스트가 포함되어 있습니다.

주의:

- 현재 `ingest`는 normalize까지 수행하며, ClickHouse insert는 아직 붙지 않았습니다.
- 따라서 현재는 `수신 + 정규화 + 검증` 단계까지 구현된 상태입니다.

## 빠른 시작

### Linux

1. Python 3.10+ 준비
2. `agent/` 배포
3. `linux/install_linux.sh` 실행
4. `sudo /opt/gpu-agent/bin/gpu-agent validate`

### Windows

1. Python 3.10+ 준비
2. 리포 또는 패키징된 agent 파일 배포
3. `windows/install_windows.ps1` 실행
4. `C:\gpu-agent\bin\gpu-agent.cmd validate`

### Kubernetes

베이스 배포:

```bash
kubectl apply -k k8s
```

테스트 오버레이 배포:

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone k8s/test | kubectl apply -f -
```

## 주요 흐름

Kubernetes / Linux GPU 노드:

```text
dcgm-exporter -> vmagent -> VictoriaMetrics
validator -> ingest -> ClickHouse
telegraf -> ingest -> ClickHouse
```

Windows:

```text
telegraf(metrics endpoint) -> vmagent -> VictoriaMetrics
telegraf(logs/events) -> ingest -> ClickHouse
gpu-agent -> local result JSON / direct event -> ingest -> ClickHouse
```

## ingest

`ingest/`는 다음 payload를 받습니다.

- `gpu-agent` / `validator`가 직접 보내는 JSON 이벤트
- `telegraf`가 보내는 `metrics` 배열 JSON

실행 예:

```bash
python3 -m ingest.server
```

Kubernetes 내부 주소:

```text
http://gpu-ingest.gpu-monitoring.svc.cluster.local:8080/events
```

## 문서

- [사용자 설명서](USER_GUIDE.md)
- [트러블슈팅 가이드](TROUBLESHOOTING.md)
- [ingest 설명](ingest/README.md)
- [K8s 테스트 오버레이 설명](k8s/test/README.md)

## 다음 단계

- `gpu-ingest`에 ClickHouse insert 추가
- Telegraf / validator event 스키마 고정
- 인증 토큰 / 고객 식별 / 중복 제거 추가
- 운영 대시보드 및 알림 룰 연결
