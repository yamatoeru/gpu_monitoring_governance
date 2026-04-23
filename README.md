# GPU Monitoring Governance Starter Kit

이 패키지는 아래 운영 모델을 기준으로 작성되었습니다.

- Windows
  - Telegraf: Windows Service
  - gpu-agent: PowerShell + Scheduled Task
- Linux
  - dcgm-exporter: systemd service
  - telegraf: systemd service
  - gpu-agent: CLI + systemd timer
- Kubernetes
  - dcgm-exporter: DaemonSet
  - telegraf: DaemonSet
  - validator: CronJob

## 구성

- `agent/`: 공통 Python CLI (`gpu-agent`)
- `linux/`: Linux systemd unit, 설치 스크립트, telegraf 설정
- `windows/`: Windows 설치/검증/스케줄러 스크립트, telegraf 설정
- `k8s/`: Kubernetes YAML (DaemonSet/CronJob/RBAC/ConfigMap)
- `examples/`: 버전 정보 예시

## 빠른 시작

### Linux

1. Python 3.10+ 준비
2. `agent/` 배포
3. `linux/install_linux.sh` 실행
4. `sudo /opt/gpu-agent/bin/gpu-agent validate`

### Windows

1. Python 3.10+ 준비
2. `agent/` 또는 패키징된 `gpu-agent.pyz/exe` 배포
3. `windows/install_windows.ps1` 실행
4. `gpu-agent validate`

### Kubernetes

1. 이미지 빌드 및 사내 Harbor 푸시
2. `k8s/` 이미지 경로와 인제스트 URL 수정
3. `kubectl apply -f k8s/`

## 운영 포인트

- `gpu-agent`는 로컬에서 `last_result.json`을 생성합니다.
- Telegraf가 이 JSON을 읽어 중앙 수집기로 전송합니다.
- K8s validator는 HTTP API로 직접 전송하도록 예시를 넣었습니다.
- 실제 운영에서는 FastAPI/Flask ingest gateway를 두고 ClickHouse에 적재하는 방식을 권장합니다.
