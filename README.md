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
- Linux 설치 스크립트에는 호스트 기반 `dcgm-exporter` 호환 서비스 자동 설치 로직이 포함되어 있습니다.
- Linux 설치 결과물은 기본적으로 `/opt/gpu-agent/bin/gpu-agent` 경로에 배치되며, 설치 스크립트는 `/usr/local/bin/gpu-agent` 심볼릭 링크를 자동 생성합니다.
- Windows 설치 결과물은 기본적으로 `C:\gpu-agent\bin\gpu-agent.cmd` 경로에 배치됩니다.
- Kubernetes에서는 `dcgm-exporter`와 `telegraf`가 분리되어 있고, Telegraf는 `dcgm-exporter`를 scrape하지 않습니다.
- Kubernetes `validator`는 direct event를 `ingest`로 전송합니다.
- Kubernetes `telegraf`는 컨테이너 로그를 읽어 `ingest`로 전송하도록 구성돼 있습니다.
- `ingest/`는 direct event와 Telegraf payload를 공통 normalized event로 바꾸는 최소 서버입니다.
- `gpu-ingest` Deployment / Service 매니페스트가 포함되어 있습니다.

주의:

- 현재 `ingest`는 normalize를 수행하며, `CLICKHOUSE_URL`이 설정되면 ClickHouse HTTP insert까지 수행합니다.
- 따라서 현재는 `수신 + 정규화 + 저장` 단계까지 구현된 상태입니다.
- Linux / Windows 기본 설정의 버전 확인 URL은 현재 GitHub raw URL입니다.
  - `https://raw.githubusercontent.com/yamatoeru/gpu_monitoring_governance/main/examples/latest_version.json`
- 운영 전환 시에는 `GPU_AGENT_LATEST_VERSION_URL`만 사내 URL로 바꾸면 같은 구조를 유지할 수 있습니다.

## 빠른 시작

설치 파일을 가져오는 가장 단순한 방법은 아래 둘 중 하나입니다.

- Git 사용 가능:

```bash
git clone https://github.com/yamatoeru/gpu_monitoring_governance.git
cd gpu_monitoring_governance
```

현재 테스트 기준 저장소 URL:

```text
https://github.com/yamatoeru/gpu_monitoring_governance
```

운영 전환 시에는 이 저장소 URL과 `GPU_AGENT_LATEST_VERSION_URL`만 사내 Git / 사내 아티팩트 저장소 기준으로 교체하면 됩니다.

- Git 사용 불가:
  - GitHub 리포지토리 화면에서 `Code` -> `Download ZIP`
  - 압축 해제 후 해당 디렉토리에서 설치 진행

## 다운로드 / 설치 소스

| 환경 | 구성요소 | 기본 소스 | 설치 방식 | 운영 전환 시 변경 지점 |
| --- | --- | --- | --- | --- |
| Linux | `gpu-agent` | 현재 GitHub 리포지토리 | 리포 다운로드 후 `linux/install_linux.sh` 실행 | 사내 Git 또는 사내 패키지 전달 경로 |
| Linux | `telegraf` | InfluxData 공식 `.deb` (`TELEGRAF_DEB_URL`) | 설치 스크립트가 다운로드 후 설치 | `TELEGRAF_DEB_URL` |
| Linux | `dcgm-exporter` | 리포에 포함된 번들 `linux/dcgm-exporter` | 설치 스크립트가 `/usr/local/bin/dcgm-exporter`로 배치 | 번들 파일 교체 또는 운영 바이너리 보존 |
| Windows | `gpu-agent` | 현재 GitHub 리포지토리 | 리포 다운로드 후 `windows/install_windows.ps1` 실행 | 사내 Git 또는 사내 패키지 전달 경로 |
| Windows | `telegraf` | InfluxData 공식 `.zip` (`TELEGRAF_ZIP_URL`) | 설치 스크립트가 다운로드 후 설치 | `TELEGRAF_ZIP_URL` |
| Kubernetes | `dcgm-exporter` | `k8s/` 매니페스트의 컨테이너 이미지 | `kubectl apply -k k8s` 또는 오버레이 배포 | 이미지 레지스트리 / 태그 |
| Kubernetes | `telegraf` | `k8s/` 매니페스트의 컨테이너 이미지 | `kubectl apply -k k8s` 또는 오버레이 배포 | 이미지 레지스트리 / 태그 |
| 공통 | agent version check | GitHub raw `examples/latest_version.json` (`GPU_AGENT_LATEST_VERSION_URL`) | `validate` 시 HTTP 또는 `file://` 조회 | `GPU_AGENT_LATEST_VERSION_URL` |

### Linux

1. Python 3.10+ 준비
2. 리포를 다운로드하거나 패키징된 설치 파일을 대상 서버에 복사
3. `linux/install_linux.sh` 실행
   이 단계는 `sudo`가 필요합니다. 설치 스크립트는 `telegraf` 패키지 설치, 호스트 기반 `dcgm-exporter` 호환 서비스 배치, `/opt/gpu-agent` 파일 배치, `/etc/default/gpu-agent` 작성, `systemd` unit/timer 등록, 서비스 enable/restart를 수행합니다.
4. `sudo gpu-agent validate`
   설치 스크립트는 `/usr/local/bin/gpu-agent` 심볼릭 링크를 자동 생성합니다. 기존 파일이나 다른 심볼릭 링크가 있으면 보존합니다.
   기본 가이드는 `sudo` 기준입니다. 일반 사용자로 실행하면 결과 파일 경로가 자동으로 `/tmp/gpu-agent-<user>`로 전환됩니다.

### Windows

1. Python 3.10+ 준비
2. 리포 ZIP 또는 패키징된 설치 파일을 Windows 서버에 복사
3. `windows/install_windows.ps1` 실행
   이 단계는 관리자 권한이 필요합니다. 설치 스크립트는 `Telegraf ZIP` 다운로드 및 `C:\Program Files\Telegraf` 설치/갱신, Windows 서비스 등록/재시작, `C:\gpu-agent` 파일 배치, Scheduled Task 생성을 수행합니다.
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

선택적 ClickHouse 환경변수:

```text
CLICKHOUSE_URL=http://clickhouse.monitoring.svc.cluster.local:8123
CLICKHOUSE_DATABASE=gpu_monitoring
CLICKHOUSE_TABLE=events
CLICKHOUSE_USER=<optional>
CLICKHOUSE_PASSWORD=<optional>
```

Kubernetes 배포에서는 `gpu-ingest-clickhouse` Secret에 위 키들을 넣으면 `gpu-ingest` Deployment가 이를 읽습니다.

## 문서

- [사용자 설명서](USER_GUIDE.md)
- [운영자 배포 체크리스트](OPERATOR_CHECKLIST.md)
- [트러블슈팅 가이드](TROUBLESHOOTING.md)
- [ingest 설명](ingest/README.md)
- [K8s 테스트 오버레이 설명](k8s/test/README.md)

## 다음 단계

- Telegraf / validator event 스키마 고정
- 인증 토큰 / 고객 식별 / 중복 제거 추가
- 운영 대시보드 및 알림 룰 연결
