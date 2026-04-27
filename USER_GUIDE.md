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

## 2-1. 클라이언트 설치 대상 목록

이 리포 기준으로 클라이언트에 설치되거나 배포되는 구성요소는 아래와 같습니다.

### Linux 클라이언트

- 설치 대상 프로그램
  - `gpu-agent`
  - `telegraf`
  - `dcgm-exporter`
- 사용하는 폴더
  - `client/agent/`
  - `client/linux/`
- 실제 설치 진입점
  - `client/linux/install_linux.sh`

### Windows 클라이언트

- 설치 대상 프로그램
  - `gpu-agent`
  - `telegraf`
- 사용하는 폴더
  - `client/agent/`
  - `client/windows/`
- 실제 설치 진입점
  - `client/windows/install_windows.ps1`

### Kubernetes 클라이언트 클러스터

- 배포 대상 구성요소
  - `dcgm-exporter`
  - `telegraf`
  - `validator`
- 사용하는 폴더
  - `client/k8s/`
- 실제 배포 진입점
  - `kubectl apply -k client/k8s`

### 클라이언트에 설치되지 않는 서버측 구성요소

- `server/ingest/`
  - `gpu-ingest` 서버 코드
- `server/k8s/`
  - 서버 클러스터에 배포하는 `gpu-ingest` 매니페스트

즉 현재 구조에서는:

- Linux 클라이언트: `gpu-agent`, `telegraf`, `dcgm-exporter`
- Windows 클라이언트: `gpu-agent`, `telegraf`
- Kubernetes 클라이언트 클러스터: `dcgm-exporter`, `telegraf`, `validator`
- 서버측 전용: `gpu-ingest`, `ClickHouse`

## 3. 설치 파일 다운로드 방법

설치 파일을 가져오는 방법은 환경에 따라 아래 셋 중 하나를 권장합니다.

### 방법 A. Git으로 직접 다운로드

Git 사용이 가능하면 가장 단순합니다.

```bash
git clone https://github.com/yamatoeru/gpu_monitoring_governance.git
cd gpu_monitoring_governance
```

현재 테스트 기준 저장소 URL:

```text
https://github.com/yamatoeru/gpu_monitoring_governance
```

운영 전환 시에는 위 URL만 사내 Git 저장소 URL로 교체하면 됩니다.

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

## 3-1. 환경별 다운로드 / 설치 소스

| 환경 | 구성요소 | 기본 소스 | 설치 방식 | 운영 전환 시 변경 지점 |
| --- | --- | --- | --- | --- |
| Linux | `gpu-agent` | 현재 GitHub 리포지토리의 `client/agent/` | 리포 다운로드 후 `client/linux/install_linux.sh` 실행 | 사내 Git 또는 사내 패키지 전달 경로 |
| Linux | `telegraf` | Debian 계열은 InfluxData 공식 `.deb`, Red Hat 계열은 공식 `.rpm` | 설치 스크립트가 distro에 맞는 패키지를 다운로드 후 설치 | `TELEGRAF_DEB_URL`, `TELEGRAF_RPM_URL` |
| Linux | `dcgm-exporter` | 리포에 포함된 번들 `client/linux/dcgm-exporter` | 설치 스크립트가 `/usr/local/bin/dcgm-exporter`로 배치 | 번들 파일 교체 또는 운영 바이너리 보존 |
| Windows | `gpu-agent` | 현재 GitHub 리포지토리의 `client/agent/` | 리포 다운로드 후 `client/windows/install_windows.ps1` 실행 | 사내 Git 또는 사내 패키지 전달 경로 |
| Windows | `telegraf` | InfluxData 공식 `.zip` (`TELEGRAF_ZIP_URL`) | 설치 스크립트가 다운로드 후 설치 | `TELEGRAF_ZIP_URL` |
| Kubernetes | `dcgm-exporter` | `client/k8s/` 매니페스트의 컨테이너 이미지 | `kubectl apply -k client/k8s` 또는 오버레이 배포 | 이미지 레지스트리 / 태그 |
| Kubernetes | `telegraf` | `client/k8s/` 매니페스트의 컨테이너 이미지 | `kubectl apply -k client/k8s` 또는 오버레이 배포 | 이미지 레지스트리 / 태그 |
| 공통 | agent / component version check | GitHub raw `examples/latest_version.json` (`GPU_AGENT_LATEST_VERSION_URL`) | `validate` 시 HTTP 또는 `file://` 조회 | `GPU_AGENT_LATEST_VERSION_URL` |

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

### 기본 버전 확인 URL

- Linux / Windows 기본 설정은 현재 아래 GitHub raw URL을 사용합니다.

```text
https://raw.githubusercontent.com/yamatoeru/gpu_monitoring_governance/main/examples/latest_version.json
```

- 이 파일에는 현재 아래 버전 기준이 포함됩니다.
  - `latest_agent_version`
  - `latest_telegraf_version_linux`
  - `latest_telegraf_version_windows`
  - `latest_dcgm_exporter_version_linux`
- `gpu-agent validate`는 이 값을 기준으로 설치된 `agent`, `telegraf`, `dcgm-exporter` 버전이 승인 버전과 같은지 확인합니다.
- 운영 전환 시에는 `GPU_AGENT_LATEST_VERSION_URL`만 사내 version endpoint로 교체하면 됩니다.
- 이 주소를 해석할 수 없는 폐쇄망 환경에서는 `validate`가 `agent_version` 체크에서 실패할 수 있습니다.
- 이 경우 운영자는 유효한 내부 URL을 제공하거나, 테스트 목적으로 로컬 `file://` 경로를 임시로 지정해야 합니다.
- `upgrade` 명령은 현재 실제 업그레이드를 수행하지 않고, 업그레이드 필요 이벤트만 남깁니다.

### 기존 dcgm-exporter 서비스가 이미 있는 경우

- Linux 설치 스크립트는 기본적으로 번들 `dcgm-exporter` 호환 바이너리와 service unit을 설치합니다.
- 기존 `dcgm-exporter` 바이너리나 `dcgm-exporter.service`가 번들 파일과 다르면 기본적으로 기존 파일을 유지합니다.
- 번들 바이너리와 unit으로 강제 교체하려면 아래 환경변수를 사용합니다.

```bash
GPU_AGENT_MANAGE_DCGM_SERVICE=true
```

## 3-2. 버전 업데이트 절차

현재 리포는 `자동 업그레이더` 방식이 아니라, 새 리포를 다시 받아 설치 스크립트나 매니페스트를 재적용하는 방식입니다.

중요:

- `gpu-agent upgrade` 명령은 현재 실제 패키지 교체를 수행하지 않습니다.
- 실제 업데이트는 `새 리포 다운로드 -> 설치 스크립트 재실행` 또는 `매니페스트 재적용`으로 진행합니다.

### Linux 업데이트

1. 새 리포를 다시 받거나 최신 변경을 pull
2. `client/linux/`로 이동
3. 설치 스크립트 재실행

```bash
cd client/linux
sudo ./install_linux.sh
```

기본 동작:

- `gpu-agent` 파일과 설정은 새 버전으로 반영
- 기존 `telegraf`가 목표 버전과 다르면 기본적으로 보존
- 기존 `dcgm-exporter` 바이너리와 unit이 번들 파일과 다르면 기본적으로 보존

기존 Telegraf를 목표 버전으로 강제 교체:

```bash
cd client/linux
sudo TELEGRAF_FORCE_VERSION=true ./install_linux.sh
```

기존 `dcgm-exporter`를 번들 파일로 강제 교체:

```bash
cd client/linux
sudo GPU_AGENT_MANAGE_DCGM_SERVICE=true ./install_linux.sh
```

업데이트 후 검증:

```bash
sudo gpu-agent validate
sudo cat /var/log/gpu-agent/last_result.json
```

### Windows 업데이트

1. 새 리포를 다시 받거나 최신 ZIP을 다시 배포
2. `client/windows/`로 이동
3. 설치 스크립트 재실행

```powershell
cd C:\gpu_monitoring_governance\client\windows
.\install_windows.ps1
```

기본 동작:

- `gpu-agent` 파일과 설정은 새 버전으로 반영
- 기존 `telegraf`가 목표 버전과 다르면 기본적으로 보존

기존 Telegraf를 목표 버전으로 강제 교체:

```powershell
$env:TELEGRAF_FORCE_VERSION = "true"
.\install_windows.ps1
```

업데이트 후 검증:

```powershell
C:\gpu-agent\bin\gpu-agent.cmd validate
Get-Content C:\gpu-agent\status\last_result.json
```

### Kubernetes 클라이언트 클러스터 업데이트

클라이언트 클러스터는 새 매니페스트를 다시 적용하는 방식으로 업데이트합니다.

기본 배포:

```bash
kubectl apply -k client/k8s
```

테스트 오버레이:

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone client/k8s/test | kubectl apply -f -
```

기본 동작:

- 새 ConfigMap, CronJob, DaemonSet 설정이 반영
- 이미지 태그가 바뀌었으면 새 Pod가 재생성됨

업데이트 후 검증:

```bash
kubectl get pods -n gpu-monitoring
kubectl get ds -n gpu-monitoring
kubectl get cronjob -n gpu-monitoring
```

## 4. Linux 사용 절차

1. Python 3.10+ 설치
2. 리포 또는 패키징된 설치 파일 다운로드 / 복사
3. 설치 실행

```bash
cd client/linux
sudo ./install_linux.sh
```

설치 시 `sudo`가 필요한 이유:

- `telegraf` 패키지 설치 또는 교체
- `/usr/local/bin/dcgm-exporter` 바이너리 배치 또는 교체
- `/opt/gpu-agent` 아래 바이너리/패키지 배치
- Debian 계열은 `/etc/default/gpu-agent`, Red Hat 계열은 `/etc/sysconfig/gpu-agent` 환경 파일 작성
- `/etc/telegraf/telegraf.d/` 설정 파일 배치
- `/etc/systemd/system/`에 unit/timer 등록
- `systemctl enable/restart/start` 수행

4. 검증 실행

```bash
sudo gpu-agent validate
```
설치 스크립트는 기본적으로 `/usr/local/bin/gpu-agent` 심볼릭 링크를 생성합니다.
기존 파일이나 다른 심볼릭 링크가 있으면 보존하고 경고만 출력합니다.

5. 결과 확인

```bash
sudo cat /var/log/gpu-agent/last_result.json
sudo cat /var/log/gpu-agent/heartbeat.json
```

기본 가이드는 `sudo` 실행 기준입니다.
일반 사용자로 실행하면 `/var/log/gpu-agent` 대신 `/tmp/gpu-agent-<user>`로 자동 전환됩니다.
이 경우 stderr에 fallback 안내가 출력됩니다.

예:

```bash
/opt/gpu-agent/bin/gpu-agent validate
cat /tmp/gpu-agent-$USER/last_result.json
```

명시적으로 결과 경로를 지정하고 싶다면 아래처럼 실행할 수도 있습니다.

```bash
GPU_AGENT_RESULT_DIR_LINUX=/tmp/gpu-agent-test /opt/gpu-agent/bin/gpu-agent validate
```

## 5. Windows 사용 절차

1. Python 3.10+ 설치
2. `gpu_monitoring_governance` 디렉토리 다운로드 또는 복사
3. PowerShell 실행 정책 우회 후 설치

```powershell
cd C:\gpu_monitoring_governance\client\windows
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

Windows도 기본 실행 파일은 `C:\gpu-agent\bin\gpu-agent.cmd`이며 PATH 등록은 자동으로 하지 않습니다.

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

### 클라이언트 클러스터 배포

```bash
kubectl apply -k client/k8s
```

### 서버 클러스터의 ingest 배포

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone server/k8s | kubectl apply -f -
```

homelab 고정 `LoadBalancer` IP를 쓰는 예:

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone server/k8s/overlays/homelab | kubectl apply -f -
```

### 테스트 오버레이 배포

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone client/k8s/test | kubectl apply -f -
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

운영 기준으로는 `ingest`를 서버 클러스터에 배포해야 합니다. `python3 -m ingest.server`는 개발/로컬 테스트용입니다.

### 서버 클러스터 배포

```bash
kubectl kustomize --load-restrictor=LoadRestrictionsNone server/k8s | kubectl apply -f -
```

기본 `server/k8s`는 내부 `ClusterIP` 기준입니다.

배포 후에는 클라이언트 클러스터의 `ingest_url`이 서버 클러스터의 `gpu-ingest` 앞단 Gateway 또는 내부 승인 endpoint를 가리키도록 설정합니다.

운영 권장 예:

```text
https://ingest.example.internal/events
```

homelab overlay 예:

```text
http://192.168.50.207:8080/events
```

### 로컬 개발 실행

```bash
cd server
python3 -m ingest.server
```

### 로컬 개발 실행 + 파일 기록

```bash
cd server
INGEST_OUTPUT_PATH=/tmp/gpu-monitoring-events.ndjson python3 -m ingest.server
```

### 로컬 개발 실행 + ClickHouse 적재

```bash
cd server
CLICKHOUSE_URL=http://clickhouse.monitoring.svc.cluster.local:8123 \
CLICKHOUSE_DATABASE=gpu_monitoring \
CLICKHOUSE_TABLE=events \
python3 -m ingest.server
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
  - 서버 클러스터 `gpu-ingest` normalized event 로그
  - `CLICKHOUSE_URL` 설정 시 ClickHouse row

## 9. 현재 한계

- `gpu-ingest`는 normalize 후 선택적으로 ClickHouse HTTP insert까지 수행합니다.
- 다만 재시도 큐, 인증, dedup, dead-letter 처리는 아직 없습니다.
- 따라서 현재 단계에서는 중앙 저장은 가능하지만 운영 신뢰성 기능은 추가 구현이 필요합니다.
