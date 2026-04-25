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

## 3. 설치 파일 다운로드 방법

설치 파일을 가져오는 방법은 환경에 따라 아래 셋 중 하나를 권장합니다.

### 방법 A. Git으로 직접 다운로드

Git 사용이 가능하면 가장 단순합니다.

```bash
git clone https://github.com/yamatoeru/gpu_monitoring_governance.git
cd gpu_monitoring_governance
```

### 방법 B. GitHub ZIP 다운로드

Git을 설치하지 않은 서버나 Windows 환경에서는 GitHub 리포지토리 화면에서 아래 순서로 받으면 됩니다.

1. GitHub 리포지토리 접속
2. `Code` 버튼 클릭
3. `Download ZIP` 선택
4. 대상 서버에 압축 해제

예시:

- Linux
  - `/opt/gpu_monitoring_governance` 등에 압축 해제
- Windows
  - `C:\gpu_monitoring_governance` 등에 압축 해제

### 방법 C. 운영자가 파일을 직접 전달

폐쇄망이나 내부 서버에서는 운영자가 미리 내려받은 리포 ZIP 또는 패키징 결과물을 대상 서버에 복사하는 방식이 적합합니다.

예시:

- Linux 서버
  - `scp`로 ZIP 또는 디렉토리 복사
- Windows 서버
  - SMB 공유 폴더, RDP 파일 복사, 사내 배포 도구 사용

다운로드 후에는 각 환경의 설치 절차를 진행합니다.

### 기존 Telegraf가 이미 설치된 경우

- Linux / Windows 설치 스크립트는 기존 Telegraf를 먼저 감지합니다.
- 기존 버전이 목표 버전과 다르면 기본 동작은 `기존 버전 유지`입니다.
- 이 경우 설치는 계속 진행되지만 경고를 출력합니다.
- 목표 버전으로 강제 교체하려면 아래 환경변수를 사용합니다.

```bash
TELEGRAF_FORCE_VERSION=true
```

Windows PowerShell:

```powershell
$env:TELEGRAF_FORCE_VERSION = "true"
```

### 기존 dcgm-exporter 서비스가 이미 있는 경우

- Linux 설치 스크립트는 기존 `dcgm-exporter.service`가 번들 unit과 다르면 기본적으로 기존 unit을 유지합니다.
- 번들 unit으로 강제 교체하려면 아래 환경변수를 사용합니다.

```bash
GPU_AGENT_MANAGE_DCGM_SERVICE=true
```

## 4. Linux 사용 절차

1. Python 3.10+ 설치
2. 리포 또는 패키징된 설치 파일 다운로드 / 복사
3. 설치 실행

```bash
cd linux
sudo ./install_linux.sh
```

설치 시 `sudo`가 필요한 이유:

- `telegraf` 패키지 설치 또는 교체
- `/opt/gpu-agent` 아래 바이너리/패키지 배치
- `/etc/default/gpu-agent` 환경 파일 작성
- `/etc/telegraf/telegraf.d/` 설정 파일 배치
- `/etc/systemd/system/`에 unit/timer 등록
- `systemctl enable/restart/start` 수행

4. 검증 실행

```bash
sudo /opt/gpu-agent/bin/gpu-agent validate
```

5. 결과 확인

```bash
sudo cat /var/log/gpu-agent/last_result.json
sudo cat /var/log/gpu-agent/heartbeat.json
```

## 5. Windows 사용 절차

1. Python 3.10+ 설치
2. `gpu_monitoring_governance` 디렉토리 다운로드 또는 복사
3. PowerShell 실행 정책 우회 후 설치

```powershell
cd C:\gpu_monitoring_governance\windows
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

설치 시 관리자 권한이 필요한 이유:

- `C:\Program Files\Telegraf` 설치 또는 교체
- `telegraf` Windows 서비스 등록/재시작
- `C:\gpu-agent` 아래 파일 배치
- Scheduled Task 생성
- 시스템 경로와 서비스 상태 확인

4. 검증 실행

```powershell
C:\gpu-agent\bin\gpu-agent.cmd validate
```

5. 결과 확인

```powershell
Get-Content C:\gpu-agent\status\last_result.json
Get-Content C:\gpu-agent\status\heartbeat.json
```

## 6. Kubernetes 사용 절차

운영자는 로컬 워크스테이션 또는 배포용 bastion 서버에 리포를 내려받은 뒤 배포합니다.

```bash
git clone https://github.com/yamatoeru/gpu_monitoring_governance.git
cd gpu_monitoring_governance
```

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

## 7. ingest 사용 절차

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

## 8. 주요 결과물

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

## 9. 현재 한계

- `gpu-ingest`는 normalize까지만 수행합니다.
- ClickHouse insert는 아직 연결되어 있지 않습니다.
- 따라서 현재 단계에서는 중앙 저장 검증이 아니라 수신 / 정규화 검증 단계입니다.
