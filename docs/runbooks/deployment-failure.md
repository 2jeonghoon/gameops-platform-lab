# 배포 실패 대응 runbook

## 목적

자동 배포 실패의 원인을 보존된 증거로 확인하고, 서비스 영향과 배포 상태를 판단한다. 배포 script는 분석 단서를 지우지 않기 위해 자동 rollback하지 않는다.

## 1. 실패 지점 확인

GitHub Actions의 `deploy` 실행에서 처음 실패한 단계를 확인한다.

- image build 또는 push: Docker build log와 GHCR package 권한을 확인한다.
- AWS 자격 증명: `AWS_DEPLOY_ROLE_ARN`, OIDC trust의 repository·branch 조건을 확인한다.
- 배포 대상 선택: project/environment tag가 붙은 실행 중 인스턴스가 정확히 하나인지 확인한다.
- SSM: 인스턴스가 `Online`인지, IAM instance profile과 SSM Agent 상태를 확인한다.
- rollout 또는 smoke test: SSM command stdout/stderr와 인스턴스 증거를 확인한다.

workflow는 SSM waiter가 끝난 뒤 `get-command-invocation` 결과를 항상 출력한다. 장기 AWS key나 SSH 접속은 이 조사 절차에 필요하지 않다.

## 2. 클러스터 상태와 증거 수집

AWS Systems Manager Session Manager로 인스턴스에 접속한 뒤 다음을 실행한다.

```bash
sudo k3s kubectl -n gameops get deployment,pods,service,ingress -o wide
sudo k3s kubectl -n gameops describe deployment game-session-api
sudo k3s kubectl -n gameops get events --sort-by=.lastTimestamp
sudo ls -lt /var/lib/gameops/evidence
sudo sed -n '1,240p' /var/lib/gameops/evidence/rollout-*.log
```

`rollout-<sha>-<utc-time>.log`에는 실패 시점의 Deployment 설명, Pod 목록, event가 저장된다. `/var/lib/gameops/evidence/previous-image`에는 배포 직전 image가 기록된다. 조사 완료 전 이 파일과 실패 Pod를 삭제하지 않는다.

현재 image와 기대 SHA를 비교한다.

```bash
sudo k3s kubectl -n gameops get deployment game-session-api \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="api")].image}{"\n"}'
```

## 3. 복구 결정

- 일시적인 registry/network 문제이고 새 revision이 정상이라면 원인을 해소한 뒤 동일 commit의 workflow를 재실행한다.
- 새 revision의 코드·설정이 원인이고 이전 ReplicaSet이 정상이라면 [rollback runbook](rollback.md)에 따라 명시적으로 되돌린다.
- 이전 revision도 불건전하면 rollback을 반복하지 말고 EC2, k3s, ingress, registry 상태를 먼저 복구한다.

복구 뒤 `/healthz`, `/readyz`, 세션 생성·조회·삭제 smoke test를 실행하고 대응 시각, 실패 SHA, 원인, 조치, 검증 결과를 운영 기록에 남긴다.
