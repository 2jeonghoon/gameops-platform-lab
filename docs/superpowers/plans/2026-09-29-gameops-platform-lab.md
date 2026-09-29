# GameOps Platform Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and document a one-week AWS-hosted k3s platform that automatically deploys, observes, stresses, recovers, and tears down a small game-session API.

**Architecture:** Terraform provisions a cost-capped single-host environment in `ap-northeast-2`; Ubuntu cloud-init installs k3s and AWS Systems Manager support. GitHub Actions tests and publishes an immutable FastAPI image to GHCR, assumes an AWS role through OIDC, and deploys through SSM. Prometheus, Grafana, Alertmanager, and optional Loki provide operational evidence for controlled incident experiments.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, prometheus-client, pytest, Ruff, Docker, Terraform, AWS VPC/EC2/IAM/Budgets/SSM, k3s, Kubernetes, Kustomize, GitHub Actions, GHCR, Prometheus, Grafana, Alertmanager, Loki, k6

**Spec:** `docs/superpowers/specs/2026-09-29-gameops-platform-lab-design.md`

## Global Constraints

- Use AWS region `ap-northeast-2`, VPC CIDR `10.20.0.0/16`, and public subnet CIDR `10.20.1.0/24`.
- Provision one Ubuntu 24.04 LTS `t3.medium` instance with a 20 GiB encrypted gp3 root volume and IMDSv2 required.
- Expose only TCP 80 publicly; do not create inbound SSH, Kubernetes API, Grafana, Prometheus, Alertmanager, or Loki rules.
- Do not create EKS, NAT Gateway, load balancer, RDS, Route 53, or ACM resources.
- Configure an AWS Budget of USD 15 with USD 5 and USD 10 notifications.
- Use local Terraform state; ignore state, plans, real tfvars, kubeconfig, credentials, and evidence containing secrets.
- Use GitHub OIDC and SSM for deployment; never store a long-lived AWS access key in GitHub.
- Tag deployed images with the immutable Git commit SHA; do not deploy `latest`.
- Run two application replicas with liveness, readiness, and startup probes plus explicit resource requests and limits.
- Treat Prometheus, Grafana, and Alertmanager as mandatory. Install Loki only if the node remains healthy under its resource budget.
- Evaluate the normal profile against HTTP 5xx below 1 percent and p95 below 250 ms.
- Complete at least two incident experiments and target all three: Pod termination, invalid image, and load degradation.
- Write user-facing documentation primarily in Korean; keep commands, identifiers, and standard technical terms in English where that improves precision.
- Record only evidence produced by actual commands and measurements. Do not imply EKS, production-scale, multi-node, or high-availability experience.
- Destroy all project-created cost-bearing AWS resources after evidence collection and verify teardown.

## Review Focus

- Invalid session input such as `player_count=0` or `player_count=101` must return HTTP 422 without creating state; Task 1 owns the tests.
- Invalid fault configuration such as a negative delay or error rate outside `0.0..1.0` must fail application startup with a clear validation error; Task 2 owns the tests.
- Any Terraform change that adds inbound SSH or exposes a port other than 80 must fail policy tests; Task 4 owns the tests.
- A nonexistent image tag must leave the previous healthy revision serving traffic and produce preserved rollout evidence before rollback; Tasks 7 and 10 own the tests.
- Teardown verification must fail when any project-tagged EC2 instance, EBS volume, public IPv4 address, or Terraform-managed resource remains; Task 11 owns the tests.

---

## Planned File Structure

```text
.dockerignore
.editorconfig
.gitignore
Makefile
README.md
pyproject.toml
uv.lock
Dockerfile
app/
  __init__.py
  main.py
  models.py
  settings.py
  store.py
  telemetry.py
tests/
  app/
    test_health.py
    test_sessions.py
    test_faults.py
    test_metrics.py
  container/
    test_container.sh
  infrastructure/
    network.tftest.hcl
    compute.tftest.hcl
    iam.tftest.hcl
    test_cloud_init.sh
  kubernetes/
    test_manifests.py
  monitoring/
    test_monitoring_config.py
  scripts/
    test_teardown_verifier.py
infra/terraform/
  versions.tf
  providers.tf
  variables.tf
  locals.tf
  network.tf
  security.tf
  budget.tf
  iam.tf
  github_oidc.tf
  compute.tf
  outputs.tf
  terraform.tfvars.example
  templates/cloud-init.yaml.tftpl
k8s/base/
  namespace.yaml
  configmap.yaml
  deployment.yaml
  service.yaml
  ingress.yaml
  kustomization.yaml
monitoring/
  kube-prometheus-stack-values.yaml
  loki-values.yaml
  service-monitor.yaml
  alerts.yaml
  dashboards/game-session-api.json
load-test/
  normal.js
  degradation.js
scripts/
  deploy_on_instance.sh
  install_observability.sh
  smoke_test.sh
  inject_fault.sh
  rollback.sh
  verify_teardown.py
.github/workflows/
  ci.yml
  deploy.yml
docs/
  architecture.md
  concepts/
  decisions/
  guides/
  runbooks/
  incidents/
  journal/
  cost.md
  security.md
  evidence-index.md
```

### Task 1: Repository Baseline and Game Session API

**Files:**
- Create: `.gitignore`, `.editorconfig`, `Makefile`, `pyproject.toml`, `uv.lock`
- Create: `app/__init__.py`, `app/main.py`, `app/models.py`, `app/settings.py`, `app/store.py`
- Create: `tests/app/test_health.py`, `tests/app/test_sessions.py`
- Create: `README.md`, `docs/journal/day-1.md`

**Interfaces:**
- Consumes: Python 3.12 and no earlier project code.
- Produces: `create_app(settings: Settings | None = None) -> FastAPI`; `Settings`; `SessionCreate(region: str, player_count: int)` with `1 <= player_count <= 100`; `Session`; `SessionStore.create(payload: SessionCreate) -> Session`; `SessionStore.get(session_id: UUID) -> Session | None`; `SessionStore.delete(session_id: UUID) -> bool`; `SessionStore.count() -> int`.

- [ ] **Step 1: Add the repository safety baseline**

Create `.gitignore` entries for `work/`, `outputs/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.terraform/`, `*.tfstate*`, `*.tfplan`, `terraform.tfvars`, `.kube/`, kubeconfig files, `.env`, credentials, and generated evidence that has not been redacted. Configure Python 3.12, FastAPI, Pydantic, Uvicorn, pytest, httpx, Ruff, PyYAML, and development commands in `pyproject.toml`; resolve exact dependency versions into `uv.lock`.

- [ ] **Step 2: Write failing health and session tests**

In `tests/app/test_health.py`, assert `GET /healthz` and `GET /readyz` return HTTP 200 with `{"status": "ok"}` and `{"status": "ready"}`. In `tests/app/test_sessions.py`, assert create/read/delete behavior, HTTP 404 for an unknown ID, and HTTP 422 for `player_count` values `0` and `101`; after either invalid request, assert the store remains empty.

- [ ] **Step 3: Run the focused tests and verify failure**

Run: `uv run pytest tests/app/test_health.py tests/app/test_sessions.py -v`

Expected: FAIL during import because `app.main.create_app` and the model/store interfaces do not exist.

- [ ] **Step 4: Implement the minimal API and in-memory store**

Implement the exact interfaces above. `POST /sessions` returns HTTP 201. `GET /sessions/{id}` returns the model. `DELETE /sessions/{id}` returns HTTP 204. Store timestamps as timezone-aware UTC values and protect the in-memory dictionary with an async lock.

- [ ] **Step 5: Run application tests and static checks**

Run: `uv run pytest tests/app/test_health.py tests/app/test_sessions.py -v`

Expected: all tests PASS.

Run: `uv run ruff check app tests && uv run ruff format --check app tests`

Expected: exit 0 with no lint or formatting errors.

- [ ] **Step 6: Document Day 1 behavior and boundaries**

Write the Korean README opening and `docs/journal/day-1.md` entries for the goal, commands, test output, in-memory-state limitation, and the reason application functionality is intentionally small.

- [ ] **Step 7: Commit the application baseline**

```bash
git add .gitignore .editorconfig Makefile pyproject.toml uv.lock app tests/app README.md docs/journal/day-1.md
git commit -m "feat: add game session API baseline"
```

### Task 2: Fault Controls and Prometheus Telemetry

**Files:**
- Modify: `app/main.py`, `app/settings.py`
- Create: `app/telemetry.py`
- Create: `tests/app/test_faults.py`, `tests/app/test_metrics.py`
- Modify: `docs/journal/day-1.md`

**Interfaces:**
- Consumes: `create_app`, `Settings`, and session routes from Task 1.
- Produces: validated `Settings(fault_delay_ms: int, fault_error_rate: float, readiness_fail: bool)`; `FaultController.apply() -> Awaitable[None]`; Prometheus endpoint `/metrics`; bounded labels `method`, `route`, and `status_class`; metrics `gameops_http_requests_total`, `gameops_http_request_duration_seconds`, `gameops_active_sessions`, `gameops_sessions_created_total`, and `gameops_sessions_deleted_total`.

- [ ] **Step 1: Write failing settings and fault tests**

Assert negative `FAULT_DELAY_MS` and `FAULT_ERROR_RATE` outside `0.0..1.0` raise a Pydantic validation error. Assert `readiness_fail=True` makes `/readyz` return HTTP 503, `fault_error_rate=1.0` makes session routes return HTTP 500, and a configured delay is observable with a fake injected sleep rather than a wall-clock assertion.

- [ ] **Step 2: Write failing telemetry tests**

Send successful, validation-error, not-found, and injected-error requests. Assert `/metrics` contains request count, request duration, active session, session-created, and session-deleted series. Assert raw session identifiers do not appear in metric label sets.

- [ ] **Step 3: Run focused tests and verify failure**

Run: `uv run pytest tests/app/test_faults.py tests/app/test_metrics.py -v`

Expected: FAIL because fault settings, controller, middleware, and `/metrics` are absent.

- [ ] **Step 4: Implement validated fault behavior and telemetry**

Implement fault delay before session-route handling, probabilistic failure using an injectable random source, readiness failure, and Prometheus instrumentation. Use route templates rather than raw request paths to prevent unbounded labels.

- [ ] **Step 5: Run the full application suite**

Run: `uv run pytest tests/app -v`

Expected: all tests PASS, including Review Focus invalid configuration cases.

- [ ] **Step 6: Commit observable fault controls**

```bash
git add app tests/app docs/journal/day-1.md
git commit -m "feat: add fault injection and service metrics"
```

### Task 3: Reproducible Container and Continuous Integration

**Files:**
- Create: `Dockerfile`, `.dockerignore`, `tests/container/test_container.sh`
- Create: `.github/workflows/ci.yml`
- Create: `docs/guides/version-matrix.md`, `docs/concepts/continuous-integration.md`
- Modify: `README.md`, `docs/journal/day-1.md`

**Interfaces:**
- Consumes: FastAPI application and tests from Tasks 1-2.
- Produces: non-root OCI image exposing port 8000 with a health check; CI status that gates later deployment; exact tool and dependency versions in `docs/guides/version-matrix.md`.

- [ ] **Step 1: Write a failing container contract test**

Create `tests/container/test_container.sh` to build `gameops-api:test`, run it as a container, assert the runtime UID is not zero, wait for Docker health status `healthy`, verify `/healthz`, `/readyz`, and `/metrics`, and remove the container in a trap.

- [ ] **Step 2: Run the container contract and verify failure**

Run: `bash tests/container/test_container.sh`

Expected: FAIL because `Dockerfile` does not exist.

- [ ] **Step 3: Implement the minimal production image**

Use a Python 3.12 slim base, install only locked runtime dependencies, copy the application, create and switch to a non-root user, expose port 8000, define the health check, and start Uvicorn with one worker.

- [ ] **Step 4: Run the container contract and vulnerability scan**

Run: `bash tests/container/test_container.sh`

Expected: PASS.

Run: `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:<version-recorded-in-version-matrix> image --exit-code 1 --ignore-unfixed --severity CRITICAL gameops-api:test`

Expected: exit 0, or a documented dependency/base-image upgrade followed by a clean rerun.

- [ ] **Step 5: Add the CI workflow**

Configure `ci.yml` for pull requests and pushes. It must run Ruff, pytest, the image build, Trivy, secret scanning, and later-discovered Terraform/Kubernetes checks only when their paths exist. Pin every third-party action to an immutable reviewed commit SHA and record the human-readable release in `version-matrix.md`.

- [ ] **Step 6: Validate the workflow locally**

Run: `actionlint .github/workflows/ci.yml`

Expected: no output and exit 0.

- [ ] **Step 7: Commit the reproducible build**

```bash
git add Dockerfile .dockerignore tests/container .github/workflows/ci.yml README.md docs
git commit -m "ci: add reproducible container checks"
```

### Task 4: Terraform Network and Cost Guardrails

**Files:**
- Create: `infra/terraform/versions.tf`, `providers.tf`, `variables.tf`, `locals.tf`
- Create: `infra/terraform/network.tf`, `security.tf`, `budget.tf`, `outputs.tf`
- Create: `infra/terraform/terraform.tfvars.example`
- Create: `tests/infrastructure/network.tftest.hcl`
- Modify: `.github/workflows/ci.yml`, `Makefile`
- Create: `docs/concepts/terraform.md`, `docs/concepts/vpc.md`, `docs/concepts/security-group.md`
- Create: `docs/decisions/002-local-terraform-state.md`
- Create: `docs/cost.md`
- Create: `docs/journal/day-2.md`

**Interfaces:**
- Consumes: AWS account access supplied outside Git and the spec's fixed network/cost values.
- Produces: Terraform variables `aws_region`, `project_name`, `environment`, `budget_alert_email`; network resource IDs; security group ID; budget guardrail; outputs `vpc_id`, `public_subnet_id`, and `app_security_group_id`.

- [ ] **Step 1: Write failing Terraform tests with a mock AWS provider**

In `network.tftest.hcl`, assert region `ap-northeast-2`, VPC `10.20.0.0/16`, subnet `10.20.1.0/24`, public-IP assignment enabled, Internet Gateway default route present, exactly one public ingress rule for TCP 80, no TCP 22 rule, budget limit `15`, and thresholds `5` and `10`.

- [ ] **Step 2: Run tests and verify failure**

Run: `terraform -chdir=infra/terraform init -backend=false && terraform -chdir=infra/terraform test`

Expected: FAIL because the Terraform configuration does not exist.

- [ ] **Step 3: Implement providers, variables, network, security, and budget**

Require a supported Terraform version with native test mock support and a pinned AWS provider constraint. Use `default_tags` for project and environment. Do not add any unapproved AWS resource.

- [ ] **Step 4: Run Terraform quality checks**

Run: `terraform -chdir=infra/terraform fmt -check -recursive`

Expected: exit 0.

Run: `terraform -chdir=infra/terraform validate && terraform -chdir=infra/terraform test`

Expected: all validations and mock tests PASS, including the no-SSH Review Focus assertion.

Add these commands to `make verify` and to a Terraform job in `ci.yml`, then validate the workflow with `actionlint .github/workflows/ci.yml`.

- [ ] **Step 5: Write concept and decision documentation**

Document Terraform state and lifecycle, VPC packet flow, stateful security groups, why port 80 is the only public ingress, why state is local for this project, and what a production remote backend would change. Record commands and outputs in `day-2.md` without account IDs or credentials.

- [ ] **Step 6: Commit network guardrails**

```bash
git add infra/terraform tests/infrastructure .github/workflows/ci.yml Makefile docs
git commit -m "feat: provision network and cost guardrails"
```

### Task 5: EC2, IAM, GitHub OIDC, and k3s Bootstrap

**Files:**
- Create: `infra/terraform/iam.tf`, `github_oidc.tf`, `compute.tf`
- Create: `infra/terraform/templates/cloud-init.yaml.tftpl`
- Modify: `infra/terraform/variables.tf`, `outputs.tf`, `terraform.tfvars.example`
- Create: `tests/infrastructure/compute.tftest.hcl`, `iam.tftest.hcl`, `test_cloud_init.sh`
- Create: `docs/concepts/k3s.md`, `docs/concepts/github-oidc.md`
- Create: `docs/decisions/001-single-node-k3s.md`, `docs/decisions/003-ssm-without-ssh.md`
- Create: `docs/architecture.md`
- Create: `docs/guides/prerequisites.md`, `docs/guides/provision.md`, `docs/guides/bootstrap-k3s.md`
- Modify: `docs/journal/day-2.md`; create `docs/journal/day-3.md`

**Interfaces:**
- Consumes: subnet and security-group IDs from Task 4; variables `github_owner` and `github_repository`.
- Produces: outputs `instance_id`, `public_ipv4`, `github_deploy_role_arn`; EC2 with SSM registration and k3s systemd service; deployment role restricted to `repo:<owner>/<repo>:ref:refs/heads/main`; deployment permissions `ec2:DescribeInstances`, `ssm:SendCommand`, `ssm:GetCommandInvocation`, and `ssm:ListCommandInvocations`, with command execution limited to `AWS-RunShellScript` and the project-tagged instance.

- [ ] **Step 1: Write failing compute and IAM tests**

Assert `t3.medium`, Ubuntu 24.04 LTS selection, encrypted 20 GiB gp3, `http_tokens = "required"`, SSM instance profile attachment, no key pair, OIDC audience `sts.amazonaws.com`, main-branch-only subject, and deployment permissions limited to instance discovery plus SSM command send/read operations.

- [ ] **Step 2: Write a failing cloud-init contract test**

Assert the rendered template installs and enables the SSM agent, installs a pinned k3s version, disables world-readable kubeconfig, installs `git`, `curl`, and Helm, writes the project bootstrap marker only after `kubectl get node` succeeds, and emits logs to cloud-init output.

- [ ] **Step 3: Run the focused infrastructure tests and verify failure**

Run: `terraform -chdir=infra/terraform test`

Expected: compute and IAM tests FAIL because resources are absent.

Run: `bash tests/infrastructure/test_cloud_init.sh`

Expected: FAIL because the template is absent.

- [ ] **Step 4: Implement compute, identity, and bootstrap resources**

Use the Canonical owner and name filters for the Ubuntu 24.04 LTS AMI. Require the exact repository name in the OIDC trust policy. Allow the deployment role to describe instances and send/read SSM commands, but grant no EC2 mutation or general infrastructure-write permissions. Restrict `ssm:SendCommand` to the `AWS-RunShellScript` document and the project-tagged instance. Pin the resolved k3s and Helm versions and record them in `version-matrix.md`.

- [ ] **Step 5: Run all infrastructure checks**

Run: `terraform -chdir=infra/terraform fmt -check -recursive && terraform -chdir=infra/terraform validate && terraform -chdir=infra/terraform test`

Expected: all tests PASS.

Run: `bash tests/infrastructure/test_cloud_init.sh`

Expected: PASS.

- [ ] **Step 6: Complete concepts and provisioning guides**

Explain k3s versus upstream Kubernetes, control plane and node roles, OIDC token exchange, SSM management without SSH, prerequisites, `plan` review, `apply`, bootstrap verification, and common cloud-init failure checks.

- [ ] **Step 7: Commit the secure host bootstrap**

```bash
git add infra/terraform tests/infrastructure docs
git commit -m "feat: bootstrap secure k3s host"
```

### Task 6: Kubernetes Workload Configuration

**Files:**
- Create: `k8s/base/namespace.yaml`, `configmap.yaml`, `deployment.yaml`
- Create: `k8s/base/service.yaml`, `ingress.yaml`, `kustomization.yaml`
- Create: `tests/kubernetes/test_manifests.py`
- Create: `scripts/smoke_test.sh`
- Modify: `.github/workflows/ci.yml`, `Makefile`
- Create: `docs/guides/deploy.md`
- Modify: `docs/journal/day-3.md`

**Interfaces:**
- Consumes: container port 8000 and health routes from Tasks 1-3; k3s ingress on EC2 port 80 from Task 5.
- Produces: namespace `gameops`; Deployment `game-session-api`; Service `game-session-api`; Ingress route `/`; ConfigMap fault keys; `scripts/smoke_test.sh <base_url>`.

- [ ] **Step 1: Write failing manifest policy tests**

Parse `kubectl kustomize k8s/base` output and assert two replicas, no `latest` image tag, all three probes with the correct routes, CPU and memory requests/limits, ClusterIP service on port 8000, ingress route `/`, and ConfigMap defaults `FAULT_DELAY_MS=0`, `FAULT_ERROR_RATE=0`, `READINESS_FAIL=false`.

- [ ] **Step 2: Run manifest tests and verify failure**

Run: `uv run pytest tests/kubernetes/test_manifests.py -v`

Expected: FAIL because manifests do not exist.

- [ ] **Step 3: Implement the Kubernetes base**

Use RollingUpdate with `maxUnavailable: 0` and `maxSurge: 1`. Add bounded resources appropriate for two API replicas on the shared `t3.medium`. Use a placeholder image that the deployment workflow must replace with an immutable SHA.

- [ ] **Step 4: Add schema and rendered-policy checks**

Run: `kubectl kustomize k8s/base | kubeconform -strict -summary -ignore-missing-schemas`

Expected: zero invalid resources.

Run: `uv run pytest tests/kubernetes/test_manifests.py -v`

Expected: PASS.

Add both manifest commands to `make verify` and the Kubernetes validation job in `ci.yml`; rerun `actionlint .github/workflows/ci.yml`.

- [ ] **Step 5: Implement the smoke-test contract**

`scripts/smoke_test.sh <base_url>` must check health, readiness, create/read/delete a session, and exit nonzero on any status or payload mismatch. Validate with a local container endpoint before AWS deployment.

- [ ] **Step 6: Commit the workload definition**

```bash
git add k8s tests/kubernetes scripts/smoke_test.sh .github/workflows/ci.yml Makefile docs
git commit -m "feat: define resilient k3s workload"
```

### Task 7: GHCR Release and SSM Deployment Workflow

**Files:**
- Create: `.github/workflows/deploy.yml`
- Create: `scripts/deploy_on_instance.sh`, `scripts/rollback.sh`
- Create: `docs/runbooks/deployment-failure.md`, `docs/runbooks/rollback.md`
- Create: `docs/journal/day-4.md`
- Modify: `docs/guides/deploy.md`, `docs/guides/version-matrix.md`, `README.md`

**Interfaces:**
- Consumes: CI success from Task 3, `github_deploy_role_arn` and instance tags from Task 5, manifests and smoke test from Task 6.
- Produces: public GHCR image `ghcr.io/<owner>/<repo>/game-session-api:<git-sha>`; SSM deployment command; `deploy_on_instance.sh <repo_url> <commit_sha> <image_ref>`; `rollback.sh <namespace> <deployment>`.

- [ ] **Step 1: Write shell and workflow contract checks**

Before implementation, make `shellcheck scripts/deploy_on_instance.sh scripts/rollback.sh` and `actionlint .github/workflows/deploy.yml` fail because files are missing. Add static assertions that the workflow requests `id-token: write`, has no AWS access-key secret reference, deploys only after CI on main, passes the Git SHA, and waits for SSM and rollout results.

- [ ] **Step 2: Implement immutable image publication**

Trigger `deploy.yml` with `workflow_run` for the `ci.yml` workflow on `main`, guard the job with `github.event.workflow_run.conclusion == 'success'`, and derive the deploy SHA from `github.event.workflow_run.head_sha`. Authenticate to GHCR with `GITHUB_TOKEN`; tag only with that full Git SHA and label the image with source revision and repository URL.

- [ ] **Step 3: Implement OIDC and SSM deployment**

Assume the Terraform output role, select exactly one running instance by project/environment tags, send `deploy_on_instance.sh` parameters through the approved SSM document, wait for completion, print command output, and fail the workflow on a non-successful SSM status.

- [ ] **Step 4: Implement instance-side rollout and visible rollback**

The deploy script checks out the exact commit, applies Kustomize output, sets the immutable image, records the previous revision, waits for rollout, and invokes the smoke test. On failure it exits nonzero without deleting evidence or silently rolling back. The rollback script runs `kubectl rollout undo`, waits for completion, and reruns the smoke test.

- [ ] **Step 5: Run local validations**

Run: `shellcheck scripts/deploy_on_instance.sh scripts/rollback.sh`

Expected: exit 0.

Run: `actionlint .github/workflows/deploy.yml`

Expected: no output and exit 0.

- [ ] **Step 6: Document deployment and rollback decisions**

Write the Korean workflow explanation, OIDC trust boundary, SSM command flow, immutable tagging, failed-evidence preservation, and exact operator rollback procedure.

- [ ] **Step 7: Commit automated delivery**

```bash
git add .github/workflows/deploy.yml scripts docs README.md
git commit -m "feat: deploy immutable images through SSM"
```

### Task 8: Metrics, Dashboards, Alerts, and Logs

**Files:**
- Create: `monitoring/kube-prometheus-stack-values.yaml`, `monitoring/loki-values.yaml`, `monitoring/service-monitor.yaml`
- Create: `monitoring/alerts.yaml`, `monitoring/dashboards/game-session-api.json`
- Create: `scripts/install_observability.sh`
- Create: `tests/monitoring/test_monitoring_config.py`
- Modify: `.github/workflows/ci.yml`, `Makefile`
- Create: `docs/concepts/observability.md`, `docs/guides/observe.md`
- Create: `docs/runbooks/high-error-rate.md`, `high-latency.md`, `target-down.md`
- Create: `docs/journal/day-5.md`

**Interfaces:**
- Consumes: `/metrics`, bounded labels, and Kubernetes namespace from Tasks 2 and 6.
- Produces: Prometheus target and rules; Grafana dashboard showing throughput, 5xx, p50/p95/p99, Pod health/restarts, CPU/memory, and session counters; Alertmanager state; optional Loki query path.

- [ ] **Step 1: Write failing monitoring configuration tests**

Assert one replica per component, short retention, explicit resource limits, no public Service type, a `ServiceMonitor` selecting the API Service and `/metrics` endpoint, dashboard queries for every required panel, alerts at `5xx > 5% for 2m`, `p95 > 250ms for 5m`, target down for `1m`, and Pod restart increase.

- [ ] **Step 2: Run tests and verify failure**

Run: `uv run pytest tests/monitoring/test_monitoring_config.py -v`

Expected: FAIL because monitoring files are absent.

- [ ] **Step 3: Implement constrained Helm values, alerts, and dashboard**

Pin chart versions in the install script and `version-matrix.md`. Disable unused components that exceed the single-node scope. Store the dashboard as provisioned JSON. Keep all Services private. Generate or retrieve the Grafana credential at deployment time; do not commit it.

- [ ] **Step 4: Implement installation and health checks**

The install script installs or upgrades charts idempotently, applies alert rules, waits for readiness, confirms Prometheus target health, confirms Grafana data-source health, and attempts Loki installation only after memory-headroom checks. It must log whether Loki was installed or skipped.

- [ ] **Step 5: Run monitoring tests and shell validation**

Run: `uv run pytest tests/monitoring/test_monitoring_config.py -v && shellcheck scripts/install_observability.sh`

Expected: all checks PASS.

Add monitoring configuration and shell validation to `make verify` and `ci.yml`; rerun `actionlint .github/workflows/ci.yml`.

- [ ] **Step 6: Write observability concepts and runbooks**

Explain metrics, logs, traces as distinct signals; Prometheus pull collection; histogram quantiles; alert pending/firing/resolved states; and the difference between an experimental objective and a production SLO. Each runbook must list trigger, impact, queries, diagnosis, mitigation, recovery check, and escalation condition.

- [ ] **Step 7: Commit the observability stack**

```bash
git add monitoring scripts/install_observability.sh tests/monitoring .github/workflows/ci.yml Makefile docs
git commit -m "feat: add service observability and alerts"
```

### Task 9: Load Profiles and Incident Automation

**Files:**
- Create: `load-test/normal.js`, `load-test/degradation.js`
- Create: `scripts/inject_fault.sh`
- Modify: `.github/workflows/ci.yml`, `Makefile`
- Create: `docs/runbooks/teardown-verification.md`
- Create: `docs/incidents/001-pod-termination.md`
- Create: `docs/incidents/002-invalid-image.md`
- Create: `docs/incidents/003-load-degradation.md`
- Create: `docs/journal/day-6.md`

**Interfaces:**
- Consumes: public API URL, fault ConfigMap, alerts, dashboards, deploy and rollback scripts.
- Produces: `k6 run -e BASE_URL=<url> load-test/normal.js`; controlled overload scenario; `inject_fault.sh <delay_ms> <error_rate> <readiness_fail>`; incident documents ready for actual timestamps and measurements.

- [ ] **Step 1: Write the normal-load profile**

Implement a fixed-duration scenario that exercises create/read/delete and enforces `http_req_failed < 0.01` and `p(95) < 250ms`. `BASE_URL` is required and the script must abort clearly if absent.

- [ ] **Step 2: Write the degradation profile**

Implement a higher-concurrency profile intended to cross the latency or error alert threshold. It must report thresholds as expected failures rather than masquerading as a normal passing test.

- [ ] **Step 3: Implement authenticated fault injection**

`inject_fault.sh` validates numeric ranges, patches the ConfigMap, restarts the Deployment, waits for rollout, and prints the resulting configuration. Reject negative delay and error rates outside `0.0..1.0` before calling kubectl.

Add k6 syntax/archive validation and `shellcheck scripts/inject_fault.sh` to `make verify` and `ci.yml`; rerun `actionlint .github/workflows/ci.yml`.

- [ ] **Step 4: Validate scripts without AWS**

Run: `k6 inspect load-test/normal.js && k6 inspect load-test/degradation.js`

Expected: both scripts parse and describe their scenarios.

Run: `shellcheck scripts/inject_fault.sh`

Expected: exit 0.

- [ ] **Step 5: Create incident document structures**

Each file must contain hypothesis, preconditions and workload, reproduction, timeline, metrics/logs/events/alerts, response, recovery, verification, root cause, and prevention. Use explicit `NOT YET EXECUTED` markers until Task 10 replaces them with actual evidence; these markers prevent draft reports from being mistaken for completed incidents.

- [ ] **Step 6: Commit experiment definitions**

```bash
git add load-test scripts/inject_fault.sh .github/workflows/ci.yml Makefile docs/incidents docs/runbooks docs/journal/day-6.md
git commit -m "test: define load and incident experiments"
```

### Task 10: Provision, Deploy, Observe, and Run Incidents

**Files:**
- Modify: `docs/journal/day-2.md` through `day-6.md`
- Modify: `docs/incidents/001-pod-termination.md`, `002-invalid-image.md`, `003-load-degradation.md`
- Create: `docs/evidence-index.md`, `docs/security.md`
- Modify: `docs/architecture.md`, `docs/guides/provision.md`, `deploy.md`, `observe.md`

**Interfaces:**
- Consumes: all code, infrastructure, workflows, scripts, and runbooks from Tasks 1-9; valid AWS credentials; confirmed budget notification email; public GitHub repository.
- Produces: a live but temporary environment, actual measurement evidence, completed incident reports, and verified recovery behavior.

- [ ] **Step 1: Run the full preflight suite**

Run: `make verify`

Expected: application, container, Terraform, Kubernetes, monitoring, shell, workflow, and secret checks all PASS before any paid resource is created.

- [ ] **Step 2: Confirm AWS identity, credit, region, and plan**

Run `aws sts get-caller-identity`, check credit expiry and budget email, then run `terraform -chdir=infra/terraform plan -out=gameops.tfplan`. Review that the plan contains only approved resource types and no SSH ingress, NAT Gateway, load balancer, RDS, EKS, Route 53, or ACM resource.

- [ ] **Step 3: Apply infrastructure and verify bootstrap**

Run `terraform -chdir=infra/terraform apply gameops.tfplan`. Through SSM, verify cloud-init completion, SSM health, k3s systemd status, node Ready status, and absence of a public Kubernetes API. Record redacted outputs in the Day 2-3 journals.

- [ ] **Step 4: Push the repository and execute CI/CD**

Create the GitHub repository only after confirming its final owner/name match the OIDC trust policy. Push main, wait for CI, publish the SHA-tagged image, deploy through SSM, and verify the public smoke flow. Record links and redacted command IDs in the evidence index.

- [ ] **Step 5: Install and verify observability**

Run the installation script through SSM. Verify Prometheus target health, Grafana data sources and every dashboard panel, Alertmanager, and Loki or the documented log fallback. Capture redacted screenshots and exact queries.

- [ ] **Step 6: Run the normal load baseline**

Run the normal k6 profile for the documented duration. Confirm 5xx below 1 percent and p95 below 250 ms, or record the measured baseline and adjust resource configuration before incidents. Never change the objective merely to make a failing run pass.

- [ ] **Step 7: Execute and document Pod termination**

Under normal load, delete one API Pod. Record detection, replacement, readiness, failed-request count, latency impact, and recovery. Replace every `NOT YET EXECUTED` marker in incident 001 with evidence.

- [ ] **Step 8: Execute and document invalid image rollout**

Deploy a nonexistent image tag. Verify the rollout fails, the previous healthy revision continues serving, the failed workflow and Kubernetes events remain available, and the rollback runbook restores a healthy rollout. Replace every draft marker in incident 002.

- [ ] **Step 9: Execute and document degradation when capacity permits**

Apply controlled delay or error injection and run the degradation profile. Capture p95, 5xx, CPU/memory, logs, and alert pending/firing/resolved transitions. Remove the fault and verify objective recovery. If time prevents this optional third incident, record the unexecuted scope honestly rather than fabricating results.

- [ ] **Step 10: Audit security and evidence**

Run secret scanning over Git history and the working tree. Confirm no AWS account ID, credentials, kubeconfig, Terraform state, Grafana password, or unredacted sensitive output is committed. Link every claim in `evidence-index.md` to a workflow, output, query, screenshot, or incident measurement.

- [ ] **Step 11: Commit verified operational evidence**

```bash
git add docs
git commit -m "docs: record verified platform operations"
```

### Task 11: Teardown, Cost Report, and Portfolio Finalization

**Files:**
- Create: `scripts/verify_teardown.py`, `tests/scripts/test_teardown_verifier.py`
- Create: `docs/guides/teardown.md`, `docs/journal/day-7.md`
- Modify: `docs/cost.md`, `docs/evidence-index.md`, `README.md`
- Modify as ignored local deliverables after measurements: `outputs/Lee_Jeonghoon_PUBG_DevOps_Resume.docx`, `outputs/Lee_Jeonghoon_PUBG_DevOps_Resume.pdf`

**Interfaces:**
- Consumes: Terraform state, AWS project tags, actual cost/credit data, evidence and measurements from Task 10.
- Produces: `verify_teardown.py --project <name> --region ap-northeast-2` with exit 0 only when no tracked or tagged cost-bearing resources remain; final public portfolio narrative; evidence-based local resume entry that is never committed with its photo or contact details.

- [ ] **Step 1: Write failing teardown-verifier tests**

Mock AWS inventory responses and assert exit failure for a remaining EC2 instance, attached or unattached project EBS volume, project public IPv4 allocation, and nonempty Terraform state. Assert exit success only when every category is empty.

- [ ] **Step 2: Run tests and verify failure**

Run: `uv run pytest tests/scripts/test_teardown_verifier.py -v`

Expected: FAIL because the verifier does not exist.

- [ ] **Step 3: Implement teardown verification**

Implement AWS inventory through the AWS CLI or SDK with exact project tags and region, plus a Terraform state-list check. Print a human-readable resource summary and return nonzero on any remaining cost-bearing resource or inventory error.

- [ ] **Step 4: Run verifier tests**

Run: `uv run pytest tests/scripts/test_teardown_verifier.py -v`

Expected: PASS.

- [ ] **Step 5: Destroy infrastructure and verify zero resources**

Run: `terraform -chdir=infra/terraform destroy`.

Expected: successful destroy.

Run: `uv run python scripts/verify_teardown.py --project gameops-platform-lab --region ap-northeast-2`.

Expected: exit 0 and zero remaining project resources. If it fails, remove only the explicitly identified project resource through Terraform or the appropriate non-destructive AWS command, then rerun.

- [ ] **Step 6: Record actual cost and final evidence**

Write estimate versus actual spend, promotional credit application, instance run hours, public IPv4 hours, and teardown time in `docs/cost.md`. Complete Day 7 and ensure the README provides a concise Korean overview, architecture diagram, reproducible commands, evidence links, limitations, and truthful learning outcomes.

- [ ] **Step 7: Update the resume only from measured evidence**

Add a concise project entry describing Terraform, AWS VPC/security groups, k3s, GitHub Actions OIDC/SSM deployment, Prometheus/Grafana, and actual incident measurements. Re-render DOCX to PNG, inspect both pages, regenerate PDF, and verify links and photo placement before replacing the existing ignored local deliverables. Confirm `outputs/` remains ignored so the public repository cannot receive the resume, photo, email address, or phone number.

- [ ] **Step 8: Run final repository verification**

Run: `make verify`

Expected: all checks PASS.

Run: `rg -n 'NOT YET EXECUTED|TBD|TODO|FIXME' README.md docs app infra k8s monitoring load-test scripts tests`

Expected: no matches, except an explicitly labeled optional third incident that was not claimed as completed.

Run: `git status --short`

Expected: only intentionally ignored local state/evidence; no uncommitted tracked files.

- [ ] **Step 9: Commit the completed portfolio project**

```bash
git add README.md scripts tests docs
git commit -m "docs: finalize GameOps platform evidence"
```
