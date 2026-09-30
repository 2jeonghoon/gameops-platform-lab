# 애플리케이션 배포

## 자동 배포 흐름

`main`의 `ci` workflow가 성공하고 repository variable `AWS_ENVIRONMENT_ACTIVE`가 문자열 `true`일 때만 `deploy` job이 실행된다. workflow는 그 CI 실행의 정확한 40자리 commit SHA를 가져와 다음 순서로 배포한다.

1. 검증이 끝난 commit을 checkout한다.
2. `ghcr.io/<owner>/<repository>/game-session-api:<git-sha>` 이미지를 build하고 GHCR에 push한다.
3. GitHub OIDC token으로 AWS 배포 역할의 단기 자격 증명을 발급받는다.
4. `Project=gameops-platform-lab`, `Environment=portfolio` tag가 붙은 실행 중 EC2가 정확히 하나인지 확인한다.
5. AWS Systems Manager Run Command로 인스턴스의 `deploy_on_instance.sh`를 실행하고 완료 상태를 기다린다.
6. 인스턴스는 같은 commit을 checkout하고 manifest의 image만 불변 SHA tag로 교체한 뒤 rollout과 smoke test를 확인한다.

workflow에는 장기 AWS access key를 저장하지 않는다. GitHub repository variable `AWS_DEPLOY_ROLE_ARN`에는 Terraform output `github_deploy_role_arn` 값을 설정한다. 인프라와 배포 대상을 확인한 뒤 `AWS_ENVIRONMENT_ACTIVE=true`로 켜고, teardown 전에 다시 `false`로 끈다. AWS 역할의 trust policy는 이 repository의 `main` branch token만 허용하고, 역할 권한은 프로젝트 tag가 붙은 인스턴스에 SSM 명령을 실행하는 범위로 제한한다. 자세한 경계는 [GitHub OIDC](../concepts/github-oidc.md)에 정리했다.

GHCR 이미지는 k3s가 별도 registry credential 없이 pull하도록 공개 package로 운영한다. 첫 image가 게시되면 GitHub Packages 설정에서 해당 container package의 visibility를 `Public`으로 바꾼다. source repository 연결과 package visibility는 서로 다른 설정이므로 둘 다 확인한다.

`latest` tag는 만들지 않는다. Git commit, container image, 배포된 workload가 같은 SHA를 공유하므로 장애 시 어떤 코드가 실행 중인지 역추적할 수 있다.

## manifest 사전 검증

```bash
kubectl kustomize k8s/base | kubeconform -strict -summary -ignore-missing-schemas
uv run pytest tests/kubernetes -v
```

Deployment는 API Pod 두 개, `maxUnavailable: 0`, `maxSurge: 1`, startup/liveness/readiness probe, CPU·memory request/limit을 정의한다. Service는 ClusterIP이며 Traefik Ingress만 `/`를 외부 TCP 80에 연결한다. Traefik NativeLB와 Service ClientIP affinity는 메모리 기반 session lifecycle을 같은 Pod에 유지하지만, 영구 상태 저장을 대신하지 않는다.

repository의 image는 `REPLACE_WITH_GIT_SHA` placeholder다. 수동으로 `latest`를 적용하지 않는다. CD workflow가 검증된 commit SHA image로 교체해야 한다.

## 배포 후 확인

```bash
kubectl -n gameops rollout status deployment/game-session-api --timeout=180s
kubectl -n gameops get pods,service,ingress
bash scripts/smoke_test.sh http://PUBLIC_IPV4
```

smoke test는 health/readiness와 세션 생성·조회·삭제 전체 흐름을 확인한다. rollout 직후 Traefik upstream 반영이 늦을 수 있어 health/readiness GET만 최대 30초 폴링한다. 중복 상태를 만들 수 있는 POST는 재시도하지 않는다. 실패하면 rollout 상태, Pod event, 이전/현재 image, application log를 보존하고 원인을 확인한다.

2026-09-30 검증된 배포는 [CI 실행](https://github.com/2jeonghoon/gameops-platform-lab/actions/runs/36680483754)과 [deploy 실행](https://github.com/2jeonghoon/gameops-platform-lab/actions/runs/36680649002)에서 확인할 수 있다.

자동 배포가 실패하면 GitHub Actions의 `Deploy through Systems Manager` 단계에 SSM stdout/stderr가 출력된다. 인스턴스의 추가 증거는 `/var/lib/gameops/evidence/`에 남는다. 자동 rollback은 하지 않으므로 증거를 먼저 확인하고 [배포 실패 runbook](../runbooks/deployment-failure.md)과 [rollback runbook](../runbooks/rollback.md)을 따른다.
