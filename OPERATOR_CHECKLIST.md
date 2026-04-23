# 운영자 배포 체크리스트

이 문서는 운영자가 중앙 수집 계층과 환경별 배포 준비를 할 때 확인해야 할 항목을 정리한 체크리스트입니다.

## 1. 아키텍처 확인

- 메트릭 경로와 로그/이벤트 경로를 분리했는지 확인
- Kubernetes / Linux GPU 노드에서는 `dcgm-exporter -> vmagent -> VictoriaMetrics` 경로를 사용
- Kubernetes / Linux GPU 노드에서는 `telegraf -> ingest -> ClickHouse` 경로를 사용
- Windows 노드에서는 `telegraf`가 메트릭과 로그를 모두 생성하고, 메트릭은 `vmagent`가 scrape하도록 설계
- `gpu-ingest`는 수신 게이트웨이이며, 현재 리포 기준으로는 normalize까지만 수행한다는 점을 운영 범위에 반영

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

### ingest

- `gpu-ingest`를 어느 클러스터 / 네임스페이스에 둘지 결정
- `Service` 주소와 DNS 명세 확정
- readiness / liveness probe 정책 확인
- stdout log 수집 여부 결정
- ClickHouse insert 추가 전까지는 normalize 로그만 남는다는 점을 운영자에게 공유

## 3. 네트워크 / 보안

- 클라이언트 환경에서 `ingest` URL 접근 가능 여부 확인
- 클라이언트 환경에서 `vmagent` scrape 또는 remote write 경로 접근 가능 여부 확인
- 방화벽 / NetworkPolicy / 사내 프록시 정책 확인
- 필요 시 TLS termination 위치 결정
- 토큰 / 헤더 기반 인증이 필요한 경우 전달 방식 정의

## 4. Kubernetes 운영 준비

- `gpu-monitoring` 네임스페이스 사용 여부 결정
- `dcgm-exporter`, `telegraf`, `validator`, `gpu-ingest` 배포 기준 정리
- GPU 노드 라벨 / nodeSelector / toleration 정책 확인
- `vmagent`가 `dcgm-exporter`를 scrape하도록 별도 매니페스트 또는 기존 운영 스택 반영
- `telegraf`가 컨테이너 로그를 읽을 수 있도록 `/var/log/containers`, `/var/log/pods` 마운트 확인
- `validator` CronJob 스케줄과 실패 보존 정책 확인
- `gpu-ingest` Service DNS를 `ingest_url`에 반영

## 5. Linux 운영 준비

- Python 3.10+ 설치 여부 확인
- NVIDIA 드라이버 / `nvidia-smi` 동작 여부 확인
- `telegraf` 자동 설치가 허용되는지 확인
- 폐쇄망이면 `TELEGRAF_DEB_URL` 사내 미러 경로 준비
- systemd 서비스 정책과 로그 보관 경로 확인

## 6. Windows 운영 준비

- Python 3.10+ 설치 여부 확인
- PowerShell 실행 정책 예외 절차 공유
- Telegraf MSI 다운로드 허용 여부 확인
- 폐쇄망이면 `TELEGRAF_MSI_URL` 사내 배포 경로 준비
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

### Linux

- `sudo /opt/gpu-agent/bin/gpu-agent validate`
- `/var/log/gpu-agent/last_result.json` 확인
- `systemctl status telegraf` 확인

### Windows

- `C:\gpu-agent\bin\gpu-agent.cmd validate`
- `C:\gpu-agent\status\last_result.json` 확인
- `Get-Service telegraf` 확인

## 9. 현재 남은 운영 작업

- `gpu-ingest`에 ClickHouse insert 추가
- 인증 / 고객 식별 / dedup / retry 정책 추가
- 운영 대시보드와 알림 룰 연결
- 장기 보관 및 재처리 전략 정리
