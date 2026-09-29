# 애플리케이션 배포

## manifest 사전 검증

```bash
kubectl kustomize k8s/base | kubeconform -strict -summary -ignore-missing-schemas
uv run pytest tests/kubernetes -v
```

Deployment는 API Pod 두 개, `maxUnavailable: 0`, `maxSurge: 1`, startup/liveness/readiness probe, CPU·memory request/limit을 정의한다. Service는 ClusterIP이며 Traefik Ingress만 `/`를 외부 TCP 80에 연결한다.

repository의 image는 `REPLACE_WITH_GIT_SHA` placeholder다. 수동으로 `latest`를 적용하지 않는다. CD workflow가 검증된 commit SHA image로 교체해야 한다.

## 배포 후 확인

```bash
kubectl -n gameops rollout status deployment/game-session-api --timeout=180s
kubectl -n gameops get pods,service,ingress
bash scripts/smoke_test.sh http://PUBLIC_IPV4
```

smoke test는 health/readiness와 세션 생성·조회·삭제 전체 흐름을 확인한다. 실패하면 rollout 상태, Pod event, 이전/현재 image, application log를 보존하고 원인을 확인한다.
