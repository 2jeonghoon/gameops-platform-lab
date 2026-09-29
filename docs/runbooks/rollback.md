# Rollback runbook

## 사용 조건

새 Deployment revision이 서비스 오류를 만들었고 직전 revision이 정상이라는 증거가 있을 때 운영자가 실행한다. 배포 실패만으로 자동 rollback하지 않는다. 자동 rollback은 실패 Pod와 event를 빠르게 없애 원인 분석을 어렵게 할 수 있기 때문이다.

## 절차

AWS Systems Manager Session Manager로 대상 EC2에 접속한다. 현재 상태와 revision을 먼저 기록한다.

```bash
cd /opt/gameops/repository
sudo k3s kubectl -n gameops rollout history deployment/game-session-api
sudo k3s kubectl -n gameops get deployment game-session-api \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="api")].image}{"\n"}'
sudo cat /var/lib/gameops/evidence/previous-image
```

이전 revision이 의도한 image인지 확인한 뒤 repository의 rollback script를 실행한다.

```bash
cd /opt/gameops/repository
sudo bash scripts/rollback.sh gameops game-session-api
```

script는 `kubectl rollout undo`를 실행하고 최대 180초 동안 완료를 기다린 뒤 `http://127.0.0.1`에 health, readiness, 세션 생성·조회·삭제 smoke test를 수행한다. 외부 주소를 검증하려면 다음과 같이 지정한다.

```bash
cd /opt/gameops/repository
sudo BASE_URL=http://PUBLIC_IPV4 bash scripts/rollback.sh gameops game-session-api
```

## 완료 확인

```bash
sudo k3s kubectl -n gameops rollout status deployment/game-session-api --timeout=180s
sudo k3s kubectl -n gameops get pods -o wide
sudo k3s kubectl -n gameops get deployment game-session-api \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="api")].image}{"\n"}'
```

rollback이 실패하면 반복 실행하지 않는다. [배포 실패 runbook](deployment-failure.md)으로 돌아가 event와 Pod 상태를 보존하고, 직전 revision 자체의 건전성과 cluster/registry 문제를 조사한다. 완료 후 실패 SHA, 복구된 SHA, 실행자, 시각, smoke test 결과를 기록한다.
