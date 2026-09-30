# Day 4 — 검증된 변경을 안전하게 전달하기

## 오늘 구현한 것

- `ci`가 성공한 `main` commit만 받는 `workflow_run` 배포 workflow
- 전체 Git SHA를 tag와 OCI revision label로 쓰는 GHCR image publication
- GitHub OIDC와 AWS IAM 역할을 이용한 단기 자격 증명
- SSH 대신 Systems Manager Run Command를 이용한 원격 배포
- 정확한 commit checkout, Kustomize render, rollout wait, API smoke test
- 실패 시 rollout 증거 보존과 운영자가 실행하는 명시적 rollback

## 이해한 핵심

CI 성공과 배포 대상 commit 사이의 연결을 느슨하게 두면 검사하지 않은 코드가 배포될 수 있다. 그래서 배포 workflow는 현재 `main`이 아니라 성공한 CI 실행의 `head_sha`를 checkout하고 같은 SHA를 image tag와 원격 checkout에 사용한다.

OIDC는 비밀 저장소에서 장기 AWS access key를 꺼내는 방식이 아니다. GitHub가 짧은 수명의 신원 token을 발급하고 AWS가 repository와 branch 조건을 검증한 뒤 제한된 역할의 임시 자격 증명을 돌려준다. 노출 가능한 장기 key가 줄고, 신뢰 대상과 권한 범위를 Terraform code로 검토할 수 있다.

SSM은 inbound SSH port 없이 관리 명령을 전달한다. 하지만 단순히 명령을 보낸 것만으로 배포 성공은 아니다. workflow가 command 완료를 기다리고 출력과 exit status를 회수해야 delivery 결과가 GitHub Actions에 정확히 반영된다.

자동 rollback은 가용성에 도움이 될 수 있지만 이번 학습 프로젝트에서는 실패 증거를 숨길 위험이 더 크다. 실패 상태를 보존하고 운영자가 근거를 확인한 뒤 rollback하도록 설계했다.

## 검증

```bash
shellcheck scripts/deploy_on_instance.sh scripts/rollback.sh
actionlint .github/workflows/deploy.yml
uv run pytest tests/scripts/test_deploy_workflow.py -v
```

정적 검사는 shell quoting·오류 처리를 확인했고, workflow 계약 테스트는 CI 성공 gate, OIDC permission, 정확한 SHA 전달, SSM waiter, 장기 AWS key 부재를 확인했다.

## Live result — 2026-09-30

실제 GitHub repository를 만든 뒤 immutable repository ID를 OIDC subject에 반영했다. AWS-managed SSM document와 project-tagged EC2 권한을 분리했고, `/bin/sh` 대신 Bash 실행, executable bit, stale clone, Kustomize mixed stream, checkout 순서 문제를 실패 로그로 진단해 수정했다.

최종 CI와 deploy가 성공했고 외부 smoke lifecycle은 12/12 통과했다. Traefik이 기본적으로 Pod IP로 직접 분산해 Service affinity를 우회한다는 사실을 확인해 NativeLB를 활성화했다. 배포 직후의 일시적 502에는 idempotent health/readiness GET만 제한 재시도하도록 보완했다.
