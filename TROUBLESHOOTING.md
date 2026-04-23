# 트러블슈팅 가이드

## 1. Windows에서 PowerShell 스크립트가 보안 오류로 실행되지 않음

증상:

- `.\install_windows.ps1` 실행 시 보안 경고 또는 실행 차단

조치:

```powershell
Unblock-File .\install_windows.ps1
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

## 2. Windows에서 `sshd` 서비스가 없음

증상:

- `Start-Service sshd` 실패
- `sshd 서비스를 찾을 수 없습니다`

원인:

- OpenSSH Server가 아직 설치되지 않음

조치:

```powershell
DISM /Online /Add-Capability /CapabilityName:OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

## 3. Windows에서 `gpu-agent validate`가 실패함

가능한 원인:

- `nvidia-smi` 없음
- `telegraf` 서비스 없음
- 버전 URL 접근 실패

확인:

```powershell
Get-Content C:\gpu-agent\status\last_result.json
Get-Service telegraf
where.exe nvidia-smi
```

## 4. Linux에서 `gpu-agent validate`가 실패함

가능한 원인:

- NVIDIA 드라이버 미설치
- `dcgm-exporter` 서비스 미기동
- `telegraf` 서비스 미기동

확인:

```bash
nvidia-smi
systemctl status dcgm-exporter
systemctl status telegraf
cat /var/log/gpu-agent/last_result.json
```

## 5. Kubernetes에서 Telegraf pod가 계속 재시작됨

확인:

```bash
kubectl logs -n gpu-monitoring -l app=telegraf --tail=100
kubectl describe pod -n gpu-monitoring -l app=telegraf
```

현재 확인된 주요 원인:

- unsupported Telegraf plugin option 사용
- `/var/log/pods` 미마운트로 컨테이너 로그 symlink 추적 실패

조치:

- `k8s/telegraf-daemonset.yaml`에 `/var/log/pods` mount 확인
- `k8s/configmap.yaml`의 Telegraf config 문법 확인

## 6. Kubernetes에서 validator가 실패함

확인:

```bash
kubectl get jobs -n gpu-monitoring
kubectl logs -n gpu-monitoring job/<job-name>
```

현재 확인된 주요 원인:

- `daemonset_telegraf` rollout 미완료
- `INGEST_URL` 잘못 설정

## 7. `gpu-ingest`가 안 뜸

확인:

```bash
kubectl get deploy,svc -n gpu-monitoring | grep gpu-ingest
kubectl logs -n gpu-monitoring deployment/gpu-ingest
kubectl describe pod -n gpu-monitoring -l app=gpu-ingest
```

health 확인:

```bash
kubectl run ingest-curl --rm -i --restart=Never -n gpu-monitoring --image=curlimages/curl:8.12.1 --command -- sh -lc "curl -fsS http://gpu-ingest:8080/health"
```

## 8. 이벤트가 ingest에 안 들어옴

확인 순서:

1. sender 설정 확인

```bash
kubectl get configmap gpu-monitoring-config -n gpu-monitoring -o yaml
```

2. validator 수동 실행

```bash
kubectl create job --from=cronjob/gpu-agent-validator -n gpu-monitoring manual-validator-$(date +%s)
```

3. ingest 로그 확인

```bash
kubectl logs -n gpu-monitoring deployment/gpu-ingest --tail=50
```

## 9. Telegraf 로그 이벤트가 안 보임

확인:

```bash
kubectl logs -n gpu-monitoring -l app=telegraf --tail=100
kubectl exec -n gpu-monitoring ds/telegraf -- ls -1 /var/log/containers
kubectl exec -n gpu-monitoring ds/telegraf -- ls -1 /var/log/pods
```

현재 확인된 중요 포인트:

- `/var/log/containers`만 마운트하면 symlink 대상인 `/var/log/pods`를 따라가지 못할 수 있음
- 두 경로를 함께 마운트해야 함

## 10. 현재 상태에서 기대해야 하는 것

현재 구현은 아래까지 완료된 상태입니다.

- sender -> ingest 수신
- payload normalize
- Kubernetes 내 `gpu-ingest` 배포

아직 미구현:

- ClickHouse insert
- 재시도 큐
- 인증 검증
- dead-letter 처리

즉 지금은 `중앙 저장 완료` 단계가 아니라 `중앙 수신 / 정규화 검증` 단계입니다.
