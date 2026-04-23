# 사용자 설명서

이 문서는 실제 사용자 또는 운영자가 이 리포를 어떤 식으로 사용하는지 설명합니다.

## 1. 목적

이 프로젝트의 목적은 다음 두 가지를 분리해서 운영하는 것입니다.

- 메트릭 수집
  - GPU / 시스템 수치 데이터
- 이벤트 / 로그 수집
  - 설치 실패, 서비스 중단, validator 결과, 운영 로그

## 2. 환경별 역할

### Kubernetes / Linux GPU 노드

- `dcgm-exporter`
  - GPU 메트릭 노출
- `vmagent`
  - `dcgm-exporter` 메트릭 scrape
- `telegraf`
  - 로그 / 이벤트 전송
- `validator`
  - 배포 상태 점검 후 정형 이벤트 전송

### Windows

- `telegraf`
  - 메트릭 생성
  - Windows 로그 / 이벤트 수집
- `vmagent`
  - Telegraf metrics endpoint scrape
- `gpu-agent`
  - 로컬 상태 점검, 결과 JSON 생성, direct event 전송 가능

## 3. Linux 사용 절차

1. Python 3.10+ 설치
2. 리포 또는 agent 파일 배포
3. 설치 실행

```bash
cd linux
sudo ./install_linux.sh
```

4. 검증 실행

```bash
sudo /opt/gpu-agent/bin/gpu-agent validate
```

5. 결과 확인

```bash
sudo cat /var/log/gpu-agent/last_result.json
sudo cat /var/log/gpu-agent/heartbeat.json
```

## 4. Windows 사용 절차

1. Python 3.10+ 설치
2. PowerShell 실행 정책 우회 후 설치

```powershell
cd C:\gpu_monitoring_governance\windows
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

3. 검증 실행

```powershell
C:\gpu-agent\bin\gpu-agent.cmd validate
```

4. 결과 확인

```powershell
Get-Content C:\gpu-agent\status\last_result.json
Get-Content C:\gpu-agent\status\heartbeat.json
```

## 5. Kubernetes 사용 절차

### 베이스 배포

```bash
kubectl apply -k k8s
```

### 테스트 오버레이 배포

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone k8s/test | kubectl apply -f -
```

### 상태 확인

```bash
kubectl get pods -n gpu-monitoring
kubectl get ds -n gpu-monitoring
kubectl get cronjob -n gpu-monitoring
kubectl get deploy,svc -n gpu-monitoring | grep gpu-ingest
```

### validator 수동 실행

```bash
kubectl create job --from=cronjob/gpu-agent-validator -n gpu-monitoring manual-validator-$(date +%s)
```

## 6. ingest 사용 절차

### 로컬 실행

```bash
python3 -m ingest.server
```

### 파일 기록 포함 실행

```bash
INGEST_OUTPUT_PATH=/tmp/gpu-monitoring-events.ndjson python3 -m ingest.server
```

### health check

```bash
curl http://127.0.0.1:8080/health
```

## 7. 주요 결과물

- Linux
  - `/var/log/gpu-agent/last_result.json`
  - `/var/log/gpu-agent/heartbeat.json`
- Windows
  - `C:\gpu-agent\status\last_result.json`
  - `C:\gpu-agent\status\heartbeat.json`
- Kubernetes
  - validator direct event
  - Telegraf log event
  - `gpu-ingest` normalized event 로그

## 8. 현재 한계

- `gpu-ingest`는 normalize까지만 수행합니다.
- ClickHouse insert는 아직 연결되어 있지 않습니다.
- 따라서 현재 단계에서는 중앙 저장 검증이 아니라 수신 / 정규화 검증 단계입니다.
